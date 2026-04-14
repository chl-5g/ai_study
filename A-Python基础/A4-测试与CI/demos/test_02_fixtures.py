"""fixture：依赖注入到测试函数参数"""


def test_user_name(sample_user):
    assert sample_user["name"] == "demo"


def test_module_counter(module_counter):
    module_counter["n"] += 1
    assert module_counter["n"] >= 1
