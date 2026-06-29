from __future__ import annotations

from tapd_testcase.models import Story, TestCase


def generate_story_1029894_cases(story: Story) -> list[TestCase]:
    """针对「获取商城积分自动存入预缴」需求生成专项测试用例。"""
    sid = story.id
    name = story.name

    return [
        TestCase(
            name=f"[{sid}] {name} - 定时任务每月27日获取商城积分",
            precondition="1. 收费系统与商城系统接口联通\n2. 测试房产已在商城产生可用积分\n3. 定时任务配置为每月27日执行",
            steps="1. 将系统时间调整至当月27日或手动触发定时任务\n2. 观察任务执行日志\n3. 查询商城接口是否被调用获取对应房产积分",
            expectation="定时任务在每月27日成功执行，正确调用商城接口并获取各房产可用积分数据",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 积分按1:1换算并存入通用预缴-零售赠送",
            precondition="1. 某房产商城可用积分为100\n2. 收费项目「通用预缴-零售赠送」已配置",
            steps="1. 触发积分获取与转换流程\n2. 查看该房产「通用预缴-零售赠送」收费项目预缴余额\n3. 查看商城该房产可用积分余额",
            expectation="100积分按1积分=1元换算，新增100元存入「通用预缴-零售赠送」收费项目；商城可用积分相应扣减100",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 积分转预缴生成实收单字段校验",
            precondition="积分转预缴流程已成功执行",
            steps="1. 查询积分转换生成的实收单\n2. 核对收费项目、支付方式、缴费来源字段",
            expectation="收费项目为「通用预缴-零售赠送」；支付方式为「零售赠送」；缴费来源为「商城」",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 零售赠送支付方式实收单不可退款作废红冲",
            precondition="存在支付方式为「零售赠送」、由积分转预缴生成的实收单",
            steps="1. 尝试对该实收单执行退款操作\n2. 尝试执行作废操作\n3. 尝试执行红冲操作",
            expectation="三种操作均被系统限制，无法完成，并给出明确提示",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 仅使用零售赠送预缴金额100元结转",
            precondition="1. 房产「通用预缴-零售赠送」余额≥100元\n2. 存在待结转的应收100元",
            steps="1. 执行预收款结转100元，仅使用零售赠送预缴金额\n2. 查看实收单（预收款结转、预收款转出）\n3. 查看预收款变动明细",
            expectation="生成预收款结转100元实收（支付方式：预收款结转）；生成预收款转出100元实收（支付方式：预收款结转）；预收款变动明细记录结转100元",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 混合使用常规预缴40元与零售赠送60元结转",
            precondition="1. 常规预缴（专项/通用）余额≥40元\n2. 通用预缴-零售赠送余额≥60元\n3. 存在待结转应收100元",
            steps="1. 执行预收款结转100元，同时使用40元常规预缴和60元零售赠送预缴\n2. 查看生成的实收单与预收款变动明细",
            expectation="分别生成60元与40元的预收款结转/转出实收；变动明细分别记录60元（零售赠送部分）和40元（常规预缴部分）",
            type="功能测试",
            priority="高",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 积分转预缴实收单推送NC编码校验",
            precondition="积分转预缴实收单已生成",
            steps="1. 触发实收单推送NC\n2. 在NC侧核对接收数据",
            expectation="实收单成功推送NC，对应编码为「通用预缴-零售赠送（SDLL2700296）」",
            type="功能测试",
            priority="中",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 商城接口异常时积分获取失败处理",
            precondition="模拟商城接口超时或返回错误",
            steps="1. 触发定时获取积分任务\n2. 观察系统异常处理与日志\n3. 检查是否产生不完整实收或错误扣减",
            expectation="任务失败有明确告警/日志；不产生错误预缴入账；不扣减商城积分；支持重试或人工介入",
            type="功能测试",
            priority="中",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 积分为0或房产无积分时不生成预缴",
            precondition="测试房产商城可用积分为0",
            steps="1. 触发积分获取与转换流程\n2. 查看预缴账户与实收单",
            expectation="不生成新的预缴入账记录和实收单；商城积分保持为0",
            type="功能测试",
            priority="中",
            story_id=sid,
            story_name=name,
        ),
        TestCase(
            name=f"[{sid}] {name} - 重复执行定时任务幂等性验证",
            precondition="当月27日已成功执行过一次积分转换",
            steps="1. 在同月再次触发定时任务\n2. 对比两次执行前后的积分与预缴余额",
            expectation="不会重复入账或重复扣减积分；系统具备幂等控制",
            type="功能测试",
            priority="中",
            story_id=sid,
            story_name=name,
        ),
    ]
