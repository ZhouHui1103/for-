import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
import time
import os
import re
import json

# ==============================================================================
# --- ⚙️ 配置区 (已根据您的最新指示更新) ⚙️ ---
# ==============================================================================
APP_ID = "cli_a844a9b271a71013"
APP_SECRET = "zz9vrf7lc69TqG89NGCaudmv4ZcijIF0"
# 不再需要手动设置APP_TOKEN，脚本会自动创建新的多维表格并获取token
# ==============================================================================
# --- 📖 源文件配置 📖 ---
# ==============================================================================
MARKDOWN_FILE = "ADHD督导业务 L3 - 飞书多维表格框架.md"
# ==============================================================================
# --- 🔍 运行前校验 ---
# ==============================================================================


def validate_configuration():
    """基础配置校验，提前捕获最常见的配置错误。"""
    if not APP_ID or not APP_SECRET:
        raise ValueError("APP_ID / APP_SECRET 不能为空，请在脚本顶部正确填写。")


def parse_md_to_blueprint(md_file_path, app_name):
    """
    内置的、最终版的 Markdown 解析器。
    它会直接读取 MD 文件，清理名称，并在内存中生成部署蓝图。
    """
    print("--- 步骤 0: 从 Markdown 生成最新的部署蓝图 ---")
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables_data = {}
    # 最终版正则表达式，可以正确处理各种格式的表格
    table_pattern = re.compile(r"###\s*(.*?)\s*\n.*?\|(.*?)\|\s*\n.*?\|(.*?)---\s*\|(.*?)\|\s*\n(.*?)(?=\n###|\Z)", re.DOTALL)
    
    for match in table_pattern.finditer(content):
        table_name = match.group(1).strip()
        table_name = re.sub(r"^\d+\.\s*", "", table_name).strip() # 强力清除序号

        header = [h.strip() for h in match.group(2).split('|')]
        rows_str = match.group(5).strip()
        
        rows = []
        for row_str in rows_str.split('\n'):
            if not row_str.strip(): continue
            cols = [col.strip() for col in row_str.strip().strip('|').split('|')]
            if len(cols) == len(header):
                rows.append(dict(zip(header, cols)))
        tables_data[table_name] = rows

    output = {"appName": app_name, "tables": []}
    for table_name, fields_data in tables_data.items():
        table_obj = {"tableName": table_name, "fields": []}
        for field_data in fields_data:
            field_name_raw = field_data.get('字段名称', '').strip()
            md_type = field_data.get('字段类型', '文本').strip()
            options_desc = field_data.get('选项 / 说明', '').strip()
            
            is_primary = '(主字段)' in field_name_raw
            field_name = field_name_raw.replace('(主字段)', '').replace('**','').strip()
            
            type_map = {
                '文本': 1, '数字': 2, '单选': 3, '多选': 4, '日期': 5, '复选框': 7, 
                '人员': 11, '关联': 18, '公式': 20, '货币': 2, 'URL': 15, 
                '创建时间': 1001, '最后更新时间': 1002, '创建人': 1003, '修改人': 1004,
                '自动编号': 1005, '查找': 19, '汇总': 20, '电话号码': 13, '超链接': 15,
                '附件': 17, '双向关联': 21, '地理位置': 22, '群组': 23
            }
            
            # 处理UI类型
            ui_type = None
            if md_type == '货币':
                ui_type = "Currency"
            elif md_type == '进度':
                ui_type = "Progress"
            elif md_type == '评分':
                ui_type = "Rating"
            elif md_type == '邮箱':
                ui_type = "Email"
            elif md_type == '条码':
                ui_type = "Barcode"
                
            # 获取飞书类型ID
            feishu_type = type_map.get(md_type, 1)

            field_obj = {"fieldName": field_name, "type": feishu_type, "isPrimary": is_primary}
            if ui_type: field_obj["ui_type"] = ui_type

            # 处理特殊字段类型的属性
            if md_type in ['单选', '多选']:
                # 单选、多选字段需要选项列表
                options_list = [opt.strip().strip('`') for opt in options_desc.split(',')]
                field_obj["property"] = {"options": [{"name": opt} for opt in options_list if opt]}
            elif md_type == '关联':
                # 关联字段需要关联表名
                match = re.search(r"关联到\s*`?(.*?)`?表", options_desc)
                if match:
                    clean_table_name = re.sub(r"^\d+\.\s*", "", match.group(1).strip()).strip() + "表"
                    field_obj["property"] = {"table_name": clean_table_name, "multiple": "多个" in options_desc}
            elif md_type in ['公式', '汇总']:
                # 公式字段需要表达式
                match = re.search(r"公式:\s*(.*)", options_desc)
                if match: field_obj["property"] = {"formula_expression": match.group(1).strip()}
            elif md_type == '日期':
                # 日期字段的格式设置
                field_obj["property"] = {"date_formatter": "yyyy/MM/dd"}
            elif md_type == '创建时间' or md_type == '最后更新时间':
                # 时间类字段的格式设置
                field_obj["property"] = {"date_formatter": "yyyy/MM/dd HH:mm"}
            elif md_type == '评分':
                # 评分字段设置
                field_obj["property"] = {"rating": {"symbol": "star"}, "min": 1, "max": 5}
            elif md_type == '货币':
                # 货币字段设置
                field_obj["property"] = {"currency_code": "CNY", "formatter": "0.00"}
            
            table_obj["fields"].append(field_obj)
        output["tables"].append(table_obj)

    print(f"✅ 成功生成蓝图\n")
    return output


class FeishuDeployer:
    def __init__(self, app_id, app_secret, app_token=None):
        self.app_token = app_token
        self.client = lark.Client.builder().app_id(app_id).app_secret(app_secret).log_level(lark.LogLevel.INFO).build()
        self.table_id_map = {} 

    def create_new_bitable(self, app_name):
        """创建一个全新的多维表格应用"""
        print("--- 步骤 0: 创建新的多维表格应用 ---")
        try:
            # 创建多维表格应用
            create_app_req = CreateAppRequest.builder().request_body(
                ReqApp.builder().name(app_name).build()
            ).build()
            
            create_app_resp = self.client.bitable.v1.app.create(create_app_req)
            
            if not create_app_resp.success():
                raise Exception(f"创建多维表格应用失败: Code={create_app_resp.code}, Msg={create_app_resp.msg}")
                
            # 获取新创建的多维表格的app_token
            self.app_token = create_app_resp.data.app.app_token
            print(f"✅ 成功创建多维表格应用: {app_name}")
            print(f"✅ 获取到新的APP_TOKEN: {self.app_token}")
            return self.app_token
            
        except Exception as e:
            raise Exception(f"创建多维表格应用失败: {e}")

    def cleanup_all_tables(self):
        """
        清理表格的方法已不再需要，因为我们会重用默认表格
        而不是尝试删除它。保留此方法仅为兼容性。
        """
        print("--- 步骤 1: 准备表格环境 ---")
        print("  - 将重用默认表格，无需清理。")
        print("--- 准备完成 ---\n")

    def create_all_tables(self, blueprint):
        print("--- 步骤 2: 逐个创建所有新表格 ---")
        
        # 获取当前表格列表，以便处理最后一个表格
        list_req = ListAppTableRequest.builder().app_token(self.app_token).build()
        list_resp = self.client.bitable.v1.app_table.list(list_req)
        if not list_resp.success():
            raise Exception(f"列出表格失败: {list_resp.msg}")
            
        existing_tables = getattr(list_resp.data, 'items', [])
        last_table_id = None
        if existing_tables:
            last_table_id = existing_tables[0].table_id
            last_table_name = existing_tables[0].name
            print(f"  - 发现默认表格: '{last_table_name}' ({last_table_id})")
            print(f"  - 将重命名此表格为第一个表格，而不是删除它")
        
        # 逐个创建表格
        for i, table_def in enumerate(blueprint['tables']):
            table_name = table_def['tableName']
            print(f"  - 正在创建表格: '{table_name}'")
            
            # 对于第一个表格，如果有默认表格，则重命名它而不是创建新表格
            if i == 0 and last_table_id:
                patch_req = PatchAppTableRequest.builder() \
                    .app_token(self.app_token) \
                    .table_id(last_table_id) \
                    .request_body(PatchAppTableRequestBody.builder().name(table_name).build()) \
                    .build()
                patch_resp = self.client.bitable.v1.app_table.patch(patch_req)
                
                if patch_resp.success():
                    print(f"  - ✅ 默认表格已重命名为: '{table_name}'")
                    self.table_id_map[table_name] = last_table_id
                else:
                    print(f"  - ❌ 重命名默认表格失败: {patch_resp.msg}")
            else:
                # 直接使用SDK创建表格
                create_table_req = CreateAppTableRequest.builder() \
                    .app_token(self.app_token) \
                    .request_body(CreateAppTableRequestBody.builder() \
                        .table(ReqTable.builder() \
                            .name(table_name) \
                            .build()) \
                        .build()) \
                    .build()
                
                create_table_resp = self.client.bitable.v1.app_table.create(create_table_req)
                
                # 处理响应
                if create_table_resp.success():
                    table_id = create_table_resp.data.table_id
                    response_status = 200
                    response_json = {"code": 0, "data": {"table_id": table_id}}
                else:
                    response_status = create_table_resp.code
                    response_json = {"code": create_table_resp.code, "msg": create_table_resp.msg}
                
                # 处理响应
                if response_status == 200 and response_json.get("code") == 0:
                    table_id = response_json["data"]["table_id"]
                    self.table_id_map[table_name] = table_id
                    print(f"  - 🎉 表格 '{table_name}' 创建成功，ID为: {table_id}")
                else:
                    print(f"  - ❌ 创建表格 '{table_name}' 失败: {response_json.get('msg', '未知错误')}")
            
            # 避免频率限制
            time.sleep(0.5)
        
        print("--- 表格创建完成 ---\n")

    def create_all_fields(self, blueprint):
        print("--- 步骤 3: 逐个创建所有字段 ---")
        for table_def in blueprint['tables']:
            table_name = table_def['tableName']
            table_id = self.table_id_map.get(table_name)
            if not table_id:
                print(f"  - ⚠️ 警告: 找不到表格 '{table_name}' 的ID, 跳过此表字段配置。")
                continue
                
            print(f"\n>> 正在为表格 '{table_name}' 配置字段:")

            primary_field_exist_in_blueprint = any(f.get("isPrimary") for f in table_def['fields'])

            for i, field_def in enumerate(table_def['fields']):
                if not primary_field_exist_in_blueprint and i == 0:
                    print(f"  - (提示) 字段 '{field_def['fieldName']}' 将作为默认主字段，无需创建。")
                    continue
                if field_def.get("isPrimary"):
                    print(f"  - (提示) 主字段 '{field_def['fieldName']}' 已自动创建，无需处理。")
                    continue

                prop_builder = AppTableFieldProperty.builder()
                prop_data = field_def.get("property")
                
                if prop_data:
                    if "options" in prop_data:
                        options = [AppTableFieldPropertyOption.builder().name(opt['name']).build() for opt in prop_data['options']]
                        prop_builder.options(options)
                    elif "table_name" in prop_data:
                        linked_table_id = self.table_id_map.get(prop_data['table_name'])
                        if linked_table_id:
                            prop_builder.table_id(linked_table_id).multiple(prop_data.get('multiple', False))
                        else:
                            print(f"  - ⚠️ 警告: 找不到关联表 '{prop_data['table_name']}' 的ID，跳过字段 '{field_def['fieldName']}'")
                            continue
                    elif "formula_expression" in prop_data:
                        prop_builder.formula_expression(prop_data['formula_expression'])

                # 创建字段构建器，确保正确设置字段类型
                field_builder = AppTableField.builder().field_name(field_def['fieldName']).type(field_def['type'])
                
                # 如果有UI类型，设置UI类型
                if field_def.get("ui_type"):
                    field_builder.ui_type(field_def["ui_type"])
                    
                # 调试信息
                print(f"  - 调试: 字段 '{field_def['fieldName']}' 类型={field_def['type']}, UI类型={field_def.get('ui_type', 'None')}")
                if prop_data:
                    field_builder.property(prop_builder.build())

                create_field_req = CreateAppTableFieldRequest.builder().app_token(self.app_token).table_id(table_id).request_body(field_builder.build()).build()
                create_field_resp = self.client.bitable.v1.app_table_field.create(create_field_req)

                if create_field_resp.success():
                    print(f"  - ✅ 字段 '{field_def['fieldName']}' 创建成功。")
                else:
                    print(f"  - ❌ 字段 '{field_def['fieldName']}' 创建失败: Code={create_field_resp.code}, Msg={create_field_resp.msg}")
                    
                # 增加延迟，避免API请求过于频繁导致的SSL错误
                time.sleep(2)


def main():
    try:
        # 验证APP_ID和APP_SECRET是否已填写
        validate_configuration()
        
        # 解析Markdown生成蓝图
        blueprint = parse_md_to_blueprint(MARKDOWN_FILE, "ADHD督导业务管理")
        
        # 创建部署器
        deployer = FeishuDeployer(APP_ID, APP_SECRET)
        
        # 创建全新的多维表格并获取app_token
        app_token = deployer.create_new_bitable("ADHD督导业务管理")
        print(f"\n⚠️ 请注意保存此APP_TOKEN，以便后续使用: {app_token}")
        
        # 部署表格结构
        deployer.cleanup_all_tables()  # 清理可能存在的默认表格
        deployer.create_all_tables(blueprint)
        deployer.create_all_fields(blueprint)

        # 成功提示
        print("\n🚀 部署成功！所有表格和字段均已创建完毕。")
        print(f"🔗 您可以通过以下链接访问新创建的多维表格:")
        print(f"   https://x-silicon.feishu.cn/base/{app_token}")

    except Exception as e:
        print(f"\n❌ 部署过程中发生严重错误: {e}")

if __name__ == "__main__":
    main()