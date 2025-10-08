import streamlit as st
import pandas as pd
import re
from typing import List, Dict, Tuple, Set


# ---------------------- 公共函数（三个实验共用）----------------------
def extract_variables(formula: str) -> List[str]:
    """提取公式中的命题变元（p/q/r/s），去重并排序"""
    variables = set()
    for char in formula:
        if char in {'p', 'q', 'r', 's'}:
            variables.add(char)
    return sorted(variables)


def generate_truth_combinations(variables: List[str]) -> List[Dict[str, str]]:
    """生成所有变元的真值组合（T/F）"""
    n = len(variables)
    combinations = []
    for i in range(2 ** n):
        combo = {}
        for j in range(n):
            bit = (i >> (n - 1 - j)) & 1
            combo[variables[j]] = 'T' if bit else 'F'
        combinations.append(combo)
    return combinations


def evaluate_formula(formula: str, truth_values: Dict[str, str]) -> str:
    """计算公式在给定真值组合下的结果（T/F），处理格式错误"""
    temp = formula
    # 替换变元为 Python 布尔值（避免子字符串替换问题）
    for var, val in truth_values.items():
        temp = re.sub(r'\b' + re.escape(var) + r'\b', 'True' if val == 'T' else 'False', temp)

    # 替换逻辑联结词
    temp = temp.replace('¬', 'not ')
    temp = temp.replace('∧', ' and ')
    temp = temp.replace('∨', ' or ')
    temp = temp.replace('→', ' <= ')  # A→B 等价于 A<=B
    temp = temp.replace('↔', ' == ')  # A↔B 等价于 A==B

    try:
        result = eval(temp)
        return 'T' if result else 'F'
    except Exception as e:
        raise ValueError(f"公式格式错误：{str(e)}（请检查括号/联结词，例：(p∧q)→r）")


# ---------------------- 实验1：命题逻辑真值表生成器 ----------------------
def truth_table_generator():
    st.header("📊 实验1：命题逻辑真值表生成器")
    st.subheader("支持功能")
    st.write("变元：p、q、r、s | 联结词：¬（否定）、∧（合取）、∨（析取）、→（蕴含）、↔（等价）")

    # 输入公式
    formula = st.text_input(
        "请输入命题公式",
        placeholder="示例：(p∧q)→r 或 p∨¬p",
        help="公式需包含至少一个变元（p/q/r/s），括号可改变优先级"
    )

    if formula:
        try:
            # 1. 提取变量
            variables = extract_variables(formula)
            if not variables:
                st.error("公式中未包含有效变元（需包含 p/q/r/s）！")
                return

            # 2. 生成真值组合 + 计算结果
            combinations = generate_truth_combinations(variables)
            results = [evaluate_formula(formula, combo) for combo in combinations]

            # 3. 整理为 DataFrame（优化展示）
            table_data = []
            for combo, res in zip(combinations, results):
                row = combo.copy()
                row[formula] = res  # 新增一列存储公式结果
                table_data.append(row)
            df = pd.DataFrame(table_data)

            # 4. 判断公式类型
            if all(res == 'T' for res in results):
                formula_type = "重言式"
                st.success(f"公式类型：{formula_type}（所有真值组合均为真）")
            elif all(res == 'F' for res in results):
                formula_type = "矛盾式"
                st.error(f"公式类型：{formula_type}（所有真值组合均为假）")
            else:
                formula_type = "可满足式（但不是重言式）"
                st.info(f"公式类型：{formula_type}（存在真值组合为真）")

            # 5. 展示真值表
            st.subheader("真值表结果")
            st.dataframe(df, use_container_width=True, hide_index=True)

        except ValueError as e:
            st.error(e)


# ---------------------- 实验2：命题公式等价性判定 ----------------------
def formula_equivalence():
    st.header("🔍 实验2：命题公式等价性判定")
    st.subheader("支持功能")
    st.write("对比两个公式的真值表，自动识别差异赋值，判定是否等价")

    # 输入两个公式
    col1, col2 = st.columns(2)
    with col1:
        formula1 = st.text_input("请输入第一个公式", placeholder="示例：p→q")
    with col2:
        formula2 = st.text_input("请输入第二个公式", placeholder="示例：¬p∨q")

    if formula1 and formula2:
        try:
            # 1. 提取所有变量（合并两个公式的变元，修正：列表转集合后求并集）
            vars1 = set(extract_variables(formula1))  # 转为集合
            vars2 = set(extract_variables(formula2))  # 转为集合
            all_vars = sorted(vars1.union(vars2))  # 集合求并集后排序

            # 2. 生成真值组合 + 计算两个公式的结果
            combinations = generate_truth_combinations(all_vars)
            results1 = [evaluate_formula(formula1, combo) for combo in combinations]
            results2 = [evaluate_formula(formula2, combo) for combo in combinations]

            # 3. 整理为对比表格
            table_data = []
            differences = []  # 存储差异赋值
            for idx, (combo, res1, res2) in enumerate(zip(combinations, results1, results2)):
                row = combo.copy()
                row[formula1] = res1
                row[formula2] = res2
                row["是否一致"] = "✅" if res1 == res2 else "❌"
                table_data.append(row)
                # 记录差异
                if res1 != res2:
                    differences.append((idx, combo, res1, res2))

            df = pd.DataFrame(table_data)
            is_equivalent = len(differences) == 0

            # 4. 展示结论
            st.subheader("等价性结论")
            if is_equivalent:
                st.success("✅ 两个公式等价（所有真值组合下结果均相同）")
            else:
                st.error(f"❌ 两个公式不等价（共 {len(differences)} 组差异赋值）")

            # 5. 展示对比真值表
            st.subheader("真值表对比")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 6. 展示差异详情（若不等价）
            if differences:
                st.subheader("差异赋值详情")
                for idx, combo, res1, res2 in differences:
                    combo_str = ", ".join([f"{k}={v}" for k, v in combo.items()])
                    st.warning(f"第 {idx + 1} 组：{combo_str} → 公式1={res1}，公式2={res2}")

        except ValueError as e:
            st.error(e)

# ---------------------- 实验4：基于逻辑的门禁系统 ----------------------
def logic_door_access():
    st.header("🚪 实验4：基于逻辑的门禁系统")
    st.subheader("准入规则")
    st.write("1. 学生：工作日工作时间需学生证，工作日非工作时间禁止")
    st.write("2. 教师：任何时间均可进入")
    st.write("3. 访客：必须有教师陪同才能进入")

    # 1. 基础输入（工作日、工作时间）
    col1, col2 = st.columns(2)
    with col1:
        W = st.radio("是否工作日", ["是", "否"], key="workday")
    with col2:
        T = st.radio("是否工作时间", ["是", "否"], key="worktime")

    # 2. 人员类型选择（动态显示后续输入）
    person_type = st.selectbox("人员类型", ["学生", "教师", "访客"], key="person")

    # 3. 动态输入（学生证/陪同，仅对应类型显示）
    C = "否"  # 学生证（默认无）
    A = "否"  # 教师陪同（默认无）
    if person_type == "学生":
        C = st.radio("是否有学生证", ["是", "否"], key="student_id")
    elif person_type == "访客":
        A = st.radio("是否有教师陪同", ["是", "否"], key="teacher_escort")

    # 4. 转换为布尔值（便于逻辑判断）
    W_bool = W == "是"
    T_bool = T == "是"
    C_bool = C == "是"
    A_bool = A == "是"
    S_bool = person_type == "学生"
    E_bool = person_type == "教师"
    V_bool = person_type == "访客"

    # 5. 逻辑推理
    allow = False
    reasoning = []  # 推理过程

    # 规则3：教师优先
    if E_bool:
        allow = True
        reasoning.append(f"1. 已知条件：工作日={W}，工作时间={T}，人员类型=教师")
        reasoning.append("2. 应用规则3：教师任何时间均可进入 → 允许进入")

    # 规则2/1：学生
    elif S_bool:
        reasoning.append(f"1. 已知条件：工作日={W}，工作时间={T}，人员类型=学生，有学生证={C}")
        if W_bool and not T_bool:
            allow = False
            reasoning.append("2. 应用规则2：工作日非工作时间 → 禁止进入")
        elif W_bool and T_bool:
            if C_bool:
                allow = True
                reasoning.append("2. 应用规则1：工作日工作时间+有学生证 → 允许进入")
            else:
                allow = False
                reasoning.append("2. 应用规则1：工作日工作时间+无学生证 → 禁止进入")
        else:
            allow = True
            reasoning.append("2. 应用默认规则：非工作日 → 允许进入")

    # 规则4：访客
    elif V_bool:
        reasoning.append(f"1. 已知条件：工作日={W}，工作时间={T}，人员类型=访客，有教师陪同={A}")
        if A_bool:
            allow = True
            reasoning.append("2. 应用规则4：有教师陪同 → 允许进入")
        else:
            allow = False
            reasoning.append("2. 应用规则4：无教师陪同 → 禁止进入")

    # 6. 展示结果
    st.subheader("推理过程")
    for step in reasoning:
        st.write(step)

    st.subheader("最终结论")
    if allow:
        st.success("✅ 可以进入实验室")
    else:
        st.error("❌ 不可以进入实验室")


# ---------------------- 主页面入口 ----------------------
def main():
    st.set_page_config(
        page_title="离散数学实验整合",
        page_icon="📚",
        layout="wide"
    )
    st.title("📚 离散数学实验整合平台")
    st.markdown("基于 Streamlit + Pandas 构建，包含三个核心实验：真值表生成、命题等价判断、门禁系统")

    # 标签页切换
    tab1, tab2, tab3 = st.tabs(["实验1：真值表生成器", "实验2：等价性判定", "实验4：门禁系统"])
    with tab1:
        truth_table_generator()
    with tab2:
        formula_equivalence()
    with tab3:
        logic_door_access()


if __name__ == "__main__":
    main()