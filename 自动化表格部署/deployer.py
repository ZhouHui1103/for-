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
            md_type_raw = field_data.get('字段类型', '文本').strip()
            options_desc = field_data.get('选项 / 说明', '').strip()
            
            # 清理字段类型，移除加粗标记(**) 和其他格式
            md_type = md_type_raw.replace('**', '').strip()
            
            is_primary = '(主字段)' in field_name_raw
            field_name = field_name_raw.replace('(主字段)', '').replace('**','').strip()
            
            # 完整的字段类型映射表
            type_map = {
                # 基础类型
                '文本': 1, '多行文本': 1, 
                '数字': 2, 
                '单选': 3, 
                '多选': 4, 
                '日期': 5, '日期时间': 5, '日期范围': 5,
                '复选框': 7, 
                '人员': 11, 
                '电话号码': 13, 
                'URL': 15, '超链接': 15, 
                '附件': 17, 
                '关联': 18, 
                '查找': 19, 
                '公式': 20, '汇总': 20, 
                '双向关联': 21, 
                '地理位置': 22, 
                '群组': 23, 
                
                # 特殊UI类型
                '货币': 2,  # 数字类型，UI类型为Currency
                '评分': 2,   # 数字类型，UI类型为Rating
                '进度': 2,   # 数字类型，UI类型为Progress
                
                # 系统字段
                '创建时间': 1001, 
                '最后更新时间': 1002, 
                '创建人': 1003, 
                '修改人': 1004,
                '自动编号': 1005
            }
            
            # 处理UI类型
            ui_type = None
            # 基础类型对应的UI类型
            ui_type_map = {
                '文本': "Text",
                '多行文本': "Text",
                '数字': "Number",
                '单选': "SingleSelect",
                '多选': "MultiSelect",
                '日期': "DateTime",
                '日期时间': "DateTime",
                '日期范围': "DateTime",
                '复选框': "Checkbox",
                '人员': "User",
                '电话号码': "Phone",
                '超链接': "Url",
                'URL': "Url",
                '附件': "Attachment",
                '关联': "SingleLink",
                '查找': "Lookup",
                '公式': "Formula",
                '汇总': "Formula",
                '双向关联': "DuplexLink",
                '地理位置': "Location",
                '群组': "GroupChat",
                '创建时间': "CreatedTime",
                '最后更新时间': "ModifiedTime",
                '创建人': "CreatedUser",
                '修改人': "ModifiedUser",
                '自动编号': "AutoNumber",
                # 特殊UI类型
                '货币': "Currency",
                '进度': "Progress",
                '评分': "Rating",
                '邮箱': "Email",
                '条码': "Barcode"
            }
            
            # 从映射表中获取UI类型
            ui_type = ui_type_map.get(md_type)
                
            # 获取飞书类型ID
            feishu_type = type_map.get(md_type.strip(), 1)
            
            # 如果类型没有正确映射，打印警告
            if md_type.strip() not in type_map:
                print(f"  - ⚠️ 警告: 字段 '{field_name}' 的类型 '{md_type}' 在映射表中不存在，默认使用文本类型(1)")
            
            # 打印调试信息，显示字段类型映射
            print(f"  - 字段映射: '{field_name}' -> 类型='{md_type}' -> 飞书类型ID={feishu_type}, UI类型={ui_type}")

            # 检查主字段类型是否合法，如果不合法则自动调整为文本类型
            if is_primary:
                allowed_primary_types = [1, 2, 5, 13, 15, 20, 22]  # 允许的主字段类型
                if feishu_type not in allowed_primary_types:
                    print(f"  - ⚠️ 警告: 主字段 '{field_name}' 的类型 '{md_type}' (ID={feishu_type}) 不允许作为主字段，自动调整为文本类型(1)")
                    feishu_type = 1  # 调整为文本类型
                    ui_type = "Text"  # 调整UI类型
            
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
                # 评分字段设置，简化处理方式
                field_obj["property"] = {"min": 1, "max": 5, "rating": {"symbol": "star"}}
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
        
    def get_field_type_name(self, type_id):
        """返回字段类型ID对应的名称，用于调试"""
        type_names = {
            1: "文本",
            2: "数字",
            3: "单选",
            4: "多选",
            5: "日期",
            7: "复选框",
            11: "人员",
            13: "电话号码",
            15: "超链接/URL",
            17: "附件",
            18: "关联",
            19: "查找",
            20: "公式/汇总",
            21: "双向关联",
            22: "地理位置",
            23: "群组",
            1001: "创建时间",
            1002: "最后更新时间",
            1003: "创建人",
            1004: "修改人",
            1005: "自动编号"
        }
        return type_names.get(type_id, f"未知类型({type_id})")

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

            # 首先获取表格当前的字段列表，以便处理主字段
            list_fields_req = ListAppTableFieldRequest.builder().app_token(self.app_token).table_id(table_id).build()
            list_fields_resp = self.client.bitable.v1.app_table_field.list(list_fields_req)
            
            existing_fields = []
            primary_field_id = None
            
            if list_fields_resp.success() and hasattr(list_fields_resp.data, 'items'):
                existing_fields = list_fields_resp.data.items
                # 找到主字段
                for field in existing_fields:
                    if field.is_primary:
                        primary_field_id = field.field_id
                        print(f"  - 找到主字段: ID={primary_field_id}, 名称={field.field_name}")
                        break
            
            # 确定哪个字段应该是主字段
            primary_field_def = None
            for field_def in table_def['fields']:
                if field_def.get("isPrimary"):
                    primary_field_def = field_def
                    break
            
            # 如果没有明确标记主字段，则使用第一个字段作为主字段
            if not primary_field_def and table_def['fields']:
                primary_field_def = table_def['fields'][0]
                print(f"  - 未找到明确标记的主字段，使用第一个字段 '{primary_field_def['fieldName']}' 作为主字段")
            
            # 如果找到了主字段ID，并且我们知道应该是什么名称，则更新它
            if primary_field_id and primary_field_def:
                print(f"  - 正在更新主字段名称为: '{primary_field_def['fieldName']}'")
                
                # 构建更新主字段的请求
                prop_builder = AppTableFieldProperty.builder()
                prop_data = primary_field_def.get("property")
                
                if prop_data:
                    if "options" in prop_data:
                        options = [AppTableFieldPropertyOption.builder().name(opt['name']).build() for opt in prop_data['options']]
                        prop_builder.options(options)
                    elif "formula_expression" in prop_data:
                        prop_builder.formula_expression(prop_data['formula_expression'])
                    elif "date_formatter" in prop_data:
                        prop_builder.date_formatter(prop_data['date_formatter'])
                    elif "rating" in prop_data:
                        # 直接设置rating属性，不使用AppTableFieldPropertyRating类
                        if "min" in prop_data:
                            prop_builder.min(prop_data["min"])
                        if "max" in prop_data:
                            prop_builder.max(prop_data["max"])
                        # 设置rating属性为包含symbol的字典
                        if "rating" in prop_data and "symbol" in prop_data["rating"]:
                            # 创建一个简单的字典来代替AppTableFieldPropertyRating对象
                            rating_dict = {"symbol": prop_data["rating"]["symbol"]}
                            prop_builder.rating(rating_dict)
                    elif "currency_code" in prop_data:
                        prop_builder.currency_code(prop_data["currency_code"])
                        if "formatter" in prop_data:
                            prop_builder.formatter(prop_data["formatter"])
                
                field_builder = AppTableField.builder().field_name(primary_field_def['fieldName']).type(primary_field_def['type'])
                
                if primary_field_def.get("ui_type"):
                    field_builder.ui_type(primary_field_def["ui_type"])
                
                # 调试信息
                print(f"  - 调试: 主字段 '{primary_field_def['fieldName']}' 类型={primary_field_def['type']}({self.get_field_type_name(primary_field_def['type'])}), UI类型={primary_field_def.get('ui_type', 'None')}")
                
                if prop_data:
                    field_builder.property(prop_builder.build())
                
                update_field_req = UpdateAppTableFieldRequest.builder() \
                    .app_token(self.app_token) \
                    .table_id(table_id) \
                    .field_id(primary_field_id) \
                    .request_body(field_builder.build()) \
                    .build()
                
                update_field_resp = self.client.bitable.v1.app_table_field.update(update_field_req)
                
                if update_field_resp.success():
                    print(f"  - ✅ 主字段 '{primary_field_def['fieldName']}' 更新成功。")
                else:
                    print(f"  - ❌ 主字段 '{primary_field_def['fieldName']}' 更新失败: Code={update_field_resp.code}, Msg={update_field_resp.msg}")
                
                time.sleep(1)  # 避免API请求过于频繁
            
                # 创建其他字段
                for i, field_def in enumerate(table_def['fields']):
                    # 如果是主字段或第一个字段（且没有明确标记的主字段），则跳过，因为已经处理过了
                    if field_def.get("isPrimary") or (i == 0 and not any(f.get("isPrimary") for f in table_def['fields'])):
                        print(f"  - 已处理字段 '{field_def['fieldName']}'，跳过创建。")
                        continue
                    
                    # 跳过查找字段(Lookup)的创建，因为它需要先创建关联字段
                    if field_def['type'] == 19 or (field_def.get('ui_type') == 'Lookup'):  # 查找字段类型
                        print(f"  - ⚠️ 警告: 字段 '{field_def['fieldName']}' 是查找字段(Lookup)类型，暂不支持自动创建，请手动添加。")
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
                        elif "date_formatter" in prop_data:
                            prop_builder.date_formatter(prop_data['date_formatter'])
                        elif "rating" in prop_data:
                            # 直接设置rating属性，不使用AppTableFieldPropertyRating类
                            if "min" in prop_data:
                                prop_builder.min(prop_data["min"])
                            if "max" in prop_data:
                                prop_builder.max(prop_data["max"])
                            # 设置rating属性为包含symbol的字典
                            if "rating" in prop_data and "symbol" in prop_data["rating"]:
                                prop_builder.rating({"symbol": prop_data["rating"]["symbol"]})
                        elif "currency_code" in prop_data:
                            prop_builder.currency_code(prop_data["currency_code"])
                            if "formatter" in prop_data:
                                prop_builder.formatter(prop_data["formatter"])

                    # 创建字段构建器，确保正确设置字段类型
                    field_builder = AppTableField.builder().field_name(field_def['fieldName']).type(field_def['type'])
                    
                    # 如果有UI类型，设置UI类型
                    if field_def.get("ui_type"):
                        field_builder.ui_type(field_def["ui_type"])
                        
                    # 调试信息
                    print(f"  - 调试: 字段 '{field_def['fieldName']}' 类型={field_def['type']}({self.get_field_type_name(field_def['type'])}), UI类型={field_def.get('ui_type', 'None')}")
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


def enable_advanced_permissions(app_token):
    """启用多维表格的高级权限"""
    print(f"\n--- 启用高级权限 ---")
    print(f"正在为多维表格 {app_token} 启用高级权限...")
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.INFO) \
            .build()
        
        # 获取当前多维表格信息
        get_app_req = GetAppRequest.builder() \
            .app_token(app_token) \
            .build()
            
        get_app_resp = client.bitable.v1.app.get(get_app_req)
        
        if not get_app_resp.success():
            print(f"❌ 获取多维表格信息失败: Code={get_app_resp.code}, Msg={get_app_resp.msg}")
            return False
            
        # 获取当前名称，保持不变
        app_name = ""
        if get_app_resp.success() and hasattr(get_app_resp.data, 'app') and hasattr(get_app_resp.data.app, 'name'):
            app_name = get_app_resp.data.app.name
        
        # 更新多维表格元数据，启用高级权限
        update_app_req = UpdateAppRequest.builder() \
            .app_token(app_token) \
            .request_body(UpdateAppRequestBody.builder()
                .name(app_name)  # 保持名称不变
                .is_advanced(True)  # 启用高级权限
                .build()) \
            .build()
            
        update_app_resp = client.bitable.v1.app.update(update_app_req)
        
        if update_app_resp.success():
            print(f"✅ 成功启用多维表格的高级权限!")
            return True
        else:
            print(f"❌ 启用高级权限失败: Code={update_app_resp.code}, Msg={update_app_resp.msg}")
            
            # 检查是否是因为不支持高级权限
            if update_app_resp.code == 1254301:
                print("⚠️ 该多维表格可能不支持开启高级权限。在线文档和电子表格中嵌入的多维表格、知识库中的多维表格不支持开启高级权限。")
            
            return False
    except Exception as e:
        print(f"❌ 启用高级权限时发生错误: {e}")
        return False

def add_admin_to_bitable(app_token, user_id, user_id_type="user_id"):
    """添加用户为多维表格的管理员"""
    print(f"\n--- 添加管理员 ---")
    print(f"正在将用户 {user_id} (类型: {user_id_type}) 添加为多维表格的管理员...")
    
    try:
        # 创建client
        client = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.INFO) \
            .build()
        
        # 首先确保启用了高级权限
        if not enable_advanced_permissions(app_token):
            print("⚠️ 警告: 无法启用高级权限，但仍将尝试添加管理员...")
            print("⚠️ 注意: 在线文档和电子表格中嵌入的多维表格、知识库中的多维表格不支持开启高级权限。")
            print("⚠️ 如果这是一个嵌入式多维表格，您可能需要先成为该多维表格的所有者或管理员。")
        
        # 获取角色ID
        admin_role_id = None
        editor_role_id = None
        
        # 获取当前多维表格的角色列表
        list_role_req = ListAppRoleRequest.builder() \
            .app_token(app_token) \
            .build()
            
        list_role_resp = client.bitable.v1.app_role.list(list_role_req)
        
        if list_role_resp.success() and hasattr(list_role_resp.data, 'items'):
            print("✅ 成功获取多维表格角色信息")
            roles = list_role_resp.data.items
            print(f"  - 发现 {len(roles)} 个角色")
            
            # 打印所有角色信息以便调试
            for i, role in enumerate(roles):
                print(f"  - 角色 {i+1}: {lark.JSON.marshal(role, indent=4)}")
                
                # 尝试获取角色ID
                if hasattr(role, 'role_id'):
                    role_id = role.role_id
                    print(f"    - 角色ID: {role_id}")
                    
                    # 根据角色ID的模式判断是管理员还是编辑者
                    # 通常第一个角色是管理员，第二个是编辑者
                    if i == 0 or (hasattr(role, 'role_type') and role.role_type == 1):
                        admin_role_id = role_id
                        print(f"    - 设置为管理员角色ID: {admin_role_id}")
                    elif i == 1 or (hasattr(role, 'role_type') and role.role_type == 2):
                        editor_role_id = role_id
                        print(f"    - 设置为编辑者角色ID: {editor_role_id}")
        else:
            print(f"⚠️ 获取多维表格角色信息失败: Code={list_role_resp.code}, Msg={list_role_resp.msg}")
            print("  - 将尝试使用默认角色ID")
        
        # 如果没有找到管理员角色ID，根据开发者文档，角色ID应该是一个字符串格式的ID
        if not admin_role_id:
            print("⚠️ 未找到明确的管理员角色ID，无法继续")
            print("请手动登录飞书，查看多维表格的角色设置，获取正确的角色ID")
            print("根据开发者文档，角色ID应该是类似 'roljRpwIUt' 的字符串格式")
            return False
        
        success = False
        
        # 尝试使用找到的管理员角色ID添加用户
        print(f"尝试使用角色ID '{admin_role_id}' 添加管理员...")
        request = CreateAppRoleMemberRequest.builder() \
            .app_token(app_token) \
            .role_id(admin_role_id) \
            .member_id_type(user_id_type) \
            .request_body(AppRoleMember.builder()
                .member_id(user_id)
                .build()) \
            .build()
        
        response = client.bitable.v1.app_role_member.create(request)
        
        if response.success():
            print(f"✅ 成功添加用户 {user_id} 为管理员!")
            return True
        else:
            print(f"❌ 使用角色ID '{admin_role_id}' 添加管理员失败: Code={response.code}, Msg={response.msg}")
            
            # 如果是角色ID不存在的错误
            if response.code == 1254047:  # RoleIdNotFound
                print("❌ 角色ID不存在，根据开发者文档，角色ID应该是类似 'roljRpwIUt' 的字符串格式")
                print("请手动登录飞书，查看多维表格的角色设置，获取正确的角色ID")
            
            # 如果单个添加失败，尝试批量添加方式
            if not success:
                print("尝试使用批量添加方式...")
                batch_request = BatchCreateAppRoleMemberRequest.builder() \
                    .app_token(app_token) \
                    .role_id(admin_role_id) \
                    .request_body(BatchCreateAppRoleMemberRequestBody.builder()
                        .member_list([AppRoleMemberId.builder()
                            .type(user_id_type)
                            .id(user_id)
                            .build()
                            ])
                        .build()) \
                    .build()
                    
                batch_response = client.bitable.v1.app_role_member.batch_create(batch_request)
                
                if batch_response.success():
                    print(f"✅ 成功批量添加用户 {user_id} 为管理员!")
                    return True
                else:
                    print(f"❌ 批量添加管理员失败: Code={batch_response.code}, Msg={batch_response.msg}")
                    
                    # 如果仍然失败，检查是否有权限问题
                    if batch_response.code == 1254301:  # OperationTypeError
                        print("\n⚠️ 错误原因: 多维表格未开启高级权限或您没有足够的权限")
                        print("请尝试以下解决方案:")
                        print("1. 确保您是多维表格的所有者或管理员")
                        print("2. 手动登录飞书，打开多维表格，在设置中启用高级权限")
                        print("3. 确认APP_TOKEN是否正确")
                        print("4. 如果是嵌入式多维表格，可能无法通过API添加管理员，请尝试通过飞书界面操作")
                    elif batch_response.code == 1254047:  # RoleIdNotFound
                        print("\n⚠️ 错误原因: 找不到指定的角色ID")
                        print("根据开发者文档，角色ID应该是类似 'roljRpwIUt' 的字符串格式")
                        print("请手动登录飞书，查看多维表格的角色设置，获取正确的角色ID")
                        
                        # 如果有编辑者角色ID，尝试添加为编辑者
                        if editor_role_id:
                            print(f"\n尝试将用户添加为编辑者(角色ID: {editor_role_id})...")
                            editor_request = CreateAppRoleMemberRequest.builder() \
                                .app_token(app_token) \
                                .role_id(editor_role_id) \
                                .member_id_type(user_id_type) \
                                .request_body(AppRoleMember.builder()
                                    .member_id(user_id)
                                    .build()) \
                                .build()
                            
                            editor_response = client.bitable.v1.app_role_member.create(editor_request)
                            
                            if editor_response.success():
                                print(f"✅ 成功添加用户 {user_id} 为编辑者!")
                                print("⚠️ 注意: 用户被添加为编辑者而非管理员")
                                return True
                            else:
                                print(f"❌ 添加编辑者也失败: Code={editor_response.code}, Msg={editor_response.msg}")
                                print("请手动登录飞书，在多维表格界面添加协作者")
                    
                    return False
        
        return success
    except Exception as e:
        print(f"❌ 添加管理员时发生错误: {e}")
        return False

def main():
    try:
        # 验证APP_ID和APP_SECRET是否已填写
        validate_configuration()
        
        # 显示菜单
        print("=== 飞书多维表格部署工具 ===")
        print("1. 创建新的多维表格")
        print("2. 添加管理员")
        print("0. 退出")
        
        choice = input("请选择功能 (默认1): ").strip() or "1"
        
        if choice == "1":
            # 创建新的多维表格
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
            
            # 询问是否添加管理员
            add_admin = input("\n是否添加管理员? (y/n): ").strip().lower()
            if add_admin == 'y':
                user_id = input("请输入用户ID: ").strip()
                user_id_type = input("请输入ID类型 (user_id/open_id/union_id/email) [默认user_id]: ").strip() or "user_id"
                add_admin_to_bitable(app_token, user_id, user_id_type)
        
        elif choice == "2":
            # 添加管理员
            app_token = input("请输入多维表格的APP_TOKEN: ").strip()
            user_id = input("请输入用户ID: ").strip()
            user_id_type = input("请输入ID类型 (user_id/open_id/union_id/email) [默认user_id]: ").strip() or "user_id"
            
            if not app_token:
                print("❌ 错误: APP_TOKEN不能为空")
                return
            
            if not user_id:
                print("❌ 错误: 用户ID不能为空")
                return
                
            add_admin_to_bitable(app_token, user_id, user_id_type)
        
        elif choice == "0":
            print("退出程序")
            return
        
        else:
            print("无效的选择")
            
    except Exception as e:
        print(f"\n❌ 部署过程中发生严重错误: {e}")

if __name__ == "__main__":
    main()