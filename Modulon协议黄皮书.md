# Modulon 协议黄皮书

**版本：0.2**

---

## 序言

本文档是 Modulon 协议的形式化技术规范，旨在为协议的实现、研究和安全审计提供一个明确、无歧义的定义。本文是《Modulon 协议白皮书》（版本 0.2）的姊妹篇，本文中出现的所有概念，其理念层面的定义均以白皮书第二章为准。本文则专注于其技术实现细节。

我们将使用一套准数学符号来定义协议的各项组件。

---

## 1. 核心数据结构

### 1.1 规范层数据结构 (Specification Layer)

规范层是协议的抽象定义世界，是所有实体行为的依据蓝图。

#### 1.1.1 模块镜像 (Module Mirror) - `Φ`

模块镜像是对一种原子化工作单元的抽象规范。

```
Φ := {
    id: UUID,          // 唯一标识符
    spec_version: SemVer, // 规范版本号
    ontology_uri: URI,   // 关联的本体论定义
    inputs: Set[TypedParam], // 输入参数类型定义集合
    outputs: Set[TypedParam],// 输出参数类型定义集合
    eval_logic: Hash,    // 指向节点评价逻辑的指针
    pricing_model: Hash, // 指向计价模型的指针
    metadata: Dict        // 元数据
}
```

**设计阐述:**
`Φ` (Phi) 是协议中最基础的“工作定义”，是不可变的“原子”。它详细定义了一项任务“是什么”以及“应遵循的规则”，但不关心“谁去做”或“如何做”。其设计旨在将“工作的定义”与“工作的执行”彻底分离，是实现互操作性的基础。

#### 1.1.2 协议 (Protocol) - `Ρ`

协议是一种复合型规范，通过编排多个模块镜像来定义一个完整的业务流程。

```
Ρ := {
    id: UUID,
    protocol_spec_version: SemVer,
    mirror_id: Φ.id,         // 协议自身对外暴露的接口，使其表现得像一个高级模块
    orchestrated_mirrors: Set[Φ.id], // 被该协议编排的子模块镜像ID集合
    rules: Hash,             // 指向编排逻辑的指针（如：状态机定义、工作流脚本）
    metadata: Dict
}
```

**设计阐述:**
`Ρ` (Rho) 是规范层的“分子”，它为一组原子化的模块 `Φ` 赋予了业务层面的意义。 
*   **核心思路**: `Ρ` 的设计核心是“编排”（Orchestration）。它不执行具体任务，而是定义任务的流程和规则。
*   **关键细节**:
    *   `mirror_id`: 此字段让协议自身也成为一个可被实现的模块。例如，一个实现了“网约车出行协议 `Ρ`”的超级节点，其本身就对外提供了一个“一键打车”的高级服务接口 `Φ`。
    *   `rules`: 这是协议的灵魂。它指向一个定义了各个 `orchestrated_mirrors` 之间如何协作的规则集。这个规则集可以是一个形式化的状态机定义，或是一个工作流描述语言（如BPMN）的脚本，它规定了任务的触发顺序、数据的传递路径和异常处理机制。

### 1.2 实体层数据结构 (Entity Layer)

实体层是协议的具象执行世界，是规范的实例化和运作。

#### 1.2.1 节点 (Node) - `Ν`

节点是实现一个或多个模块镜像的、可提供服务的实体。

```
Ν := {
    id: Address,         // 节点的唯一地址（如：公钥）
    owner: Address,      // 节点所有者的地址
    mirrors: Set[Φ.id],  // 该节点实现的模块镜像ID集合
    state: NodeState,    // 节点状态 (Active, Inactive, Deprecated)
    rating: Mapping[Φ.id, RatingScore], // 节点在各模块下的评级分数
    endpoint: URI,       // 节点的实际调用地址
    stake: Balance       // 节点的质押金
}
```

**设计阐述:**
`Ν` (Nu) 是协议中的“工作者”和“服务提供商”。它是将抽象规范转化为具体服务的活跃实体。其设计核心是建立一个开放、免许可、且有经济激励和声誉机制的服务市场。

#### 1.2.2 项目 (Project) - `Π`

项目是一个将需求、规范和执行者绑定的、具备生命周期的一次性工作实例。

```
Π := {
    id: UUID,            // 项目唯一标识符
    initiator: Address,  // 项目发起方地址
    mirror_id: Φ.id,     // 此次实例化的模块镜像ID
    assigned_node: Ν.id, // 被指派执行此项目的节点ID
    inputs: Dict,        // 实际输入的数据
    state: ProjectState, // 项目状态 (Initiated, InProgress, Completed, Failed, InDispute)
    tx_log: List[Tx]     // 相关的交易记录
}
```

**设计阐述:**
`Π` (Pi) 是协议经济模型中价值交换和状态流转的基本单位。它将一次协作的全部要素（“谁”的需求，“什么”任务，“谁来做”）固化为一个可被追踪和管理的状态机，是实现自动、可信结算的基础。

#### 1.2.3 项目 (`Π`) 与 任务 (Task) 的关系

在形式化定义中，“任务 (Task)”是一个逻辑概念，而非链上核心数据结构。它代表了对单个原子模块 `Φ` 的一次执行。

- **定义:** 一个任务 `τ` (Tau) 是一个元组 `(Π.id, Φ.id, Ν.id)`，表示在项目 `Π` 的上下文中，由节点 `Ν` 执行模块 `Φ` 的具体工作。

- **关系:**
    - 若一个项目 `Π` 的 `mirror_id` 直接指向一个原子模块 `Φ_A`，则该项目仅包含一个任务：`τ = (Π.id, Φ_A.id, Π.assigned_node)`。
    - 若一个项目 `Π` 的 `mirror_id` 指向一个复合协议 `Ρ`，该 `Ρ` 编排了模块集 `{Φ_1, Φ_2, ...}`。则该项目 `Π` 包含一个任务集合 `{τ_1, τ_2, ...}`。项目 `Π` 的 `assigned_node` 字段此时可能为空，具体的任务分配 `(Φ_i -> Ν_j)` 由协议编译器（见第4章）在项目初始化时确定，并记录在 `Π` 的扩展数据或相关日志中。

因此，`Π` 是管理状态和价值的**契约容器**，而 `τ` 是容器内的**执行单元**。

### 1.3 其他核心结构

#### 1.3.1 资产 (Asset) - `Α`

资产是协议中价值的通用载体。

```
Α := {
    id: UUID,
    type: AssetType,     // 资产类型 (e.g., FungibleToken, NFT, DataCredential)
    owner: Address,      // 资产当前的所有者地址
    metadata: Dict
}
```

**设计阐述:**
`Α` (Alpha) 的抽象设计确保了协议的价值层具有最大通用性，能与不同的经济体系集成。

---

## 2. 世界状态 (World State) - `Μ`

Modulon 的世界状态 `Μ` 是一个包含了协议中所有核心对象集合的元组。

`Μ := (S_Φ, S_Ρ, S_Ν, S_Π, S_Α)`

其中：
*   `S_Φ`: 所有模块镜像 `Φ` 的集合。
*   `S_Ρ`: 所有协议 `Ρ` 的集合。
*   `S_Ν`: 所有节点 `Ν` 的集合。
*   `S_Π`: 所有项目 `Π` 的集合。
*   `S_Α`: 所有资产 `Α` 的集合。

**设计阐述:**
`Μ` (Mu) 是对整个 Modulon 协议在特定时间点的完整快照。此定义的更新，将“协议” `Ρ` 纳入了顶层状态集，承认了“业务流程的定义”本身也是协议状态的重要组成部分。

---

## 3. 状态转移函数 (State Transition Function) - `Ξ`

状态转移函数 `Ξ` 定义了 Modulon 协议的动态行为。它接受当前状态 `Μ` 和一个交易 `T` 作为输入，并输出一个新的状态 `Μ'`。

`Μ' = Ξ(Μ, T)`

**设计阐述:**
`Ξ` (Xi) 是 Modulon 协议的“引擎”或“物理定律”。以下是触发状态改变的核心交易类型。

### 3.1 `T_deploy_mirror` (部署模块镜像)
此交易用于创建一个新的模块镜像 `Φ`。
*   `T_deploy_mirror := (sender, new_Φ_data)`
*   **转移逻辑:** `S_Φ' = S_Φ ∪ {new_Φ}`

**逻辑说明:** 这是协议原子能力的创新来源。

### 3.2 `T_deploy_protocol` (部署协议)
此交易用于创建一个新的协议 `Ρ`。
*   `T_deploy_protocol := (sender, new_Ρ_data)`
*   **转移逻辑:** `S_Ρ' = S_Ρ ∪ {new_Ρ}`

**逻辑说明:** 这是协议业务流程的创新来源。它允许社区定义新的、复杂的商业协作模式。交易有效性检查需要验证 `new_Ρ_data` 中所有的 `orchestrated_mirrors` 的 `id` 都已存在于 `S_Φ` 中。

### 3.3 `T_register_node` (注册节点)
此交易用于创建一个新的节点 `Ν`。
*   `T_register_node := (sender, new_Ν_data)`
*   **转移逻辑:** `S_Ν' = S_Ν ∪ {new_Ν}`. 需验证质押金 `new_Ν.stake` 已被锁定。

**逻辑说明:** 这是服务供给的入口。

### 3.4 `T_init_project` (初始化项目)
此交易用于根据某个模块镜像 `Φ` 创建一个新项目 `Π`。
*   `T_init_project := (sender, Π_data)`
*   **转移逻辑:** `S_Π' = S_Π ∪ {new_Π}`. 需验证、匹配并锁定资产。

**逻辑说明:** 这是需求与供给匹配、工作正式开始的标志。

### 3.5 `T_complete_project` (完成项目)
此交易由被指派的节点 `Ν` 发起，用以宣告项目完成。
*   `T_complete_project := (sender, Π.id, outputs_data)`
*   **转移逻辑:** 变更 `Π`, `Α`, `Ν` 的状态。

**逻辑说明:** 这是工作闭环和价值结算的关键步骤。

---

## 4. 协议编译：从 `Ρ` 到 `{Ν}` 的优化选择

当一个基于复杂协议 `Ρ` 的项目被初始化时（见 `T_init_project`），协议需要一个机制来将抽象的 `Ρ` “编译”成一个具体的、经优化的执行节点集合 `{Ν_1, Ν_2, ...}`。这个过程并非状态转移的一部分，而是一个在交易触发前由客户端或特定服务节点执行的计算过程。其推导遵循效率第一性原理。

该过程可以被建模为一个带权重的**集合覆盖问题 (Set Cover Problem)** 的启发式求解。

### 4.1 算法输入

- `Ρ_id`: 目标协议的 `UUID`。
- `S_Φ`, `S_Ρ`, `S_Ν`: 当前的世界状态子集。
- `W`: 一个权重向量 `(w_cost, w_rating, w_cohesion)`，用于定义优化目标。

### 4.2 编译过程

**步骤 1: 模块镜像递归解析 (Recursive Resolution)**

定义函数 `Resolve(p_id, S_Φ, S_Ρ)`，输入一个协议ID，输出其包含的所有原子模块镜像ID的扁平化集合。

1.  令 `Φ_required = ∅`。
2.  获取 `Ρ_target = S_Ρ[p_id]`。
3.  对于 `Ρ_target.orchestrated_mirrors` 中的每一个 `m_id`：
    a. 如果 `m_id` 存在于 `S_Ρ` 中（即它是一个嵌套协议），则递归调用 `Resolve(m_id, S_Φ, S_Ρ)`，并将其结果并入 `Φ_required`。
    b. 如果 `m_id` 存在于 `S_Φ` 中，则直接将其加入 `Φ_required`。
4.  返回 `Φ_required`。

**步骤 2: 候选节点集生成 (Candidate Generation)**

1.  令 `Φ_uncovered = Resolve(Ρ_id, S_Φ, S_Ρ)`。
2.  令 `Ν_candidate_pool = {Ν | Ν ∈ S_Ν and Ν.mirrors ∩ Φ_uncovered ≠ ∅}`。即所有能实现至少一个所需模块的节点池。

**步骤 3: 贪心算法选择节点 (Greedy Selection)**

这是一个启发式优化过程，旨在找到一个成本效益高的“近似最优解”。

1.  令 `Ν_selected = ∅`。
2.  **while** `Φ_uncovered` is not empty **do**:
    a. 对于 `Ν_candidate_pool` 中的每一个节点 `Ν_i`，计算其“边际效益分” `Score(Ν_i)`。
       ```
       // 计算该节点能覆盖多少个“未覆盖”的模块
       Φ_covered_by_i = Ν_i.mirrors ∩ Φ_uncovered
       num_covered = |Φ_covered_by_i|

       // 如果不能覆盖任何新模块，则跳过
       if num_covered == 0: continue

       // 计算该节点执行这些模块的平均成本和平均评级
       avg_cost = Σ(pricing_model(Φ_j)) / num_covered for Φ_j in Φ_covered_by_i
       avg_rating = Σ(Ν_i.rating[Φ_j]) / num_covered for Φ_j in Φ_covered_by_i

       // 核心：内聚性奖励。覆盖的模块越多，奖励越高，鼓励节点合并
       cohesion_bonus = num_covered ^ 2

       // 综合评分
       Score(Ν_i) = (w_rating * avg_rating + w_cohesion * cohesion_bonus) / (w_cost * avg_cost)
       ```
    b. 选择 `Ν_best`，使其 `Score` 最高。
    c. 将 `Ν_best` 加入 `Ν_selected`。
    d. 从 `Φ_uncovered` 中移除 `Ν_best` 所覆盖的所有模块：`Φ_uncovered = Φ_uncovered \ Ν_best.mirrors`。
    e. （可选）将 `Ν_best` 从 `Ν_candidate_pool` 中移除。
3.  **end while**

### 4.3 编译输出

- `Ν_selected`: 最终被选定的、用于执行该协议所有任务的节点集合。
- `Assignment`: 一个映射关系，`Mapping[Φ.id, Ν.id]`，明确每个模块由哪个选定的节点负责。

此输出结果随后被用于构造一个或多个 `T_init_project` 交易，从而在实体层启动整个协作流程。

---

## 5. 协议栈与元规范 (Protocol Stack & Meta-Specifications)

Modulon 协议栈定义了确保互操作性所需的一系列标准化规范，分布于四个逻辑层级。

### 5.1 L2 - 模块元基座层 (Module Metabase Layer)

此层定义了系统的核心“词法”与“语法”。

- **`OntologySpec`**: 定义领域知识图谱的结构，如 `Class`, `Property`, `Relation`。
- **`ModuleSpec`**: 定义 `Φ` 和 `Ρ` 的数据结构，是本黄皮书的核心。
- **`AssetSpec`**: 定义资产 `Α` 的接口。包含变种：
  - `FungibleAsset := { type: "Fungible", contract: Address, standard: "ERC20" }`
  - `NonFungibleAsset := { type: "NFT", contract: Address, tokenId: UInt, standard: "ERC721" }`
- **`PricingSpec`**: 定义 `Φ.pricing_model` 指针可以解析的计价模型结构。包含变种：
  - `FixedPricing := { type: "Fixed", amount: Balance }`
  - `TimeBasedPricing := { type: "TimeBased", rate: Balance, unit: TimeUnit }`
  - `ShareBasedPricing := { type: "ShareBased", percentage: Float, target: Asset.id }`

### 5.2 L3 - 模块排布层 (Module Arrangement Layer)

此层定义了模块如何“动态”组合与交互。

- **`WorkflowSpec`**: 定义 `Ρ.rules` 指针可以解析的编排逻辑。包含变种：
  - `FSMWorkflow := { states: Set[State], transitions: Set[Transition] }`
  - `ScriptedWorkflow := { language: "JS/WASM", script: Hash }`
- **`MonitoringSpec`**: 定义了节点必须提供的标准监控接口，如 `GetStatus()`, `GetMetrics()`。
- **`TestRatingSpec`**: 定义了 `Φ.eval_logic` 指针可以解析的评价逻辑，其输出必须为一个标准化的 `RatingScore` 结构。

### 5.3 L4 - 协议运作层 (Protocol Operation Layer)

此层定义了协议的“应用层”商业逻辑。

- **`ProjectSpec`**: 定义 `Π.state` 的枚举值 `ProjectState` 及其合法的状态转移路径。
- **`NodeMatchingSpec`**: 定义了第4章所述的协议编译算法的接口和默认实现。
- **`DisputeResolutionSpec`**: 定义了当 `Π.state` 进入 `InDispute` 时，需要调用的仲裁协议 `Ρ_dispute` 的接口规范。

---

## 6. 附录：符号表

*   `Μ`: Modulon 世界状态
*   `Φ`: 模块镜像 (Module Mirror)
*   `Ρ`: 协议 (Protocol)
*   `Ν`: 节点 (Node)
*   `Π`: 项目 (Project)
*   `Α`: 资产 (Asset)
*   `S_x`: 对象 `x` 的集合
*   `Ξ`: 状态转移函数
*   `T`: 交易 (Transaction)
