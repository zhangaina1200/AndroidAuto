"""
AndroidAuto Scheduler Module

定时任务调度器 - 基于 APScheduler + SQLite 持久化
选择理由：
1. APScheduler 是轻量级库，无外部依赖
2. 支持持久化任务，重启后自动恢复
3. 支持多种调度器（BlockingScheduler 适合后台运行）
4. 跨平台兼容性好
"""
import os
import sys
import time
import random
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import operations as ops


class ScheduleConfig:
    """调度配置管理"""

    def __init__(self, config_path):
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 多时间窗口配置
        self.time_windows = self.config.get('time_windows', [])
        if not self.time_windows:
            # 兼容旧配置格式
            self.time_windows = [self.config.get('time_window', {})]

        # 验证所有时间窗口
        self._validate_time_config()

        # 目标配置
        self.target_app = self.config.get('target', {}).get('app_package')
        self.device_serial = self.config.get('device', {}).get('serial')

        # 重试配置
        retry_config = self.config.get('retry', {})
        self.max_retries = retry_config.get('max_attempts', 5)
        self.retry_interval = retry_config.get('interval_seconds', 10)

        # 日志目录
        self.log_dir = self.config.get('logging', {}).get('dir', 'schedules')

    def _parse_time(self, t):
        """解析 HH:MM 格式时间"""
        parts = t.split(':')
        if len(parts) != 2:
            raise ValueError(f"时间格式错误: {t}，期望 HH:MM")
        return int(parts[0]), int(parts[1])

    def _validate_time_config(self):
        """验证时间配置格式"""
        for i, window in enumerate(self.time_windows):
            start = window.get('start', '09:00')
            end = window.get('end', '11:30')

            start_h, start_m = self._parse_time(start)
            end_h, end_m = self._parse_time(end)

            if start_h < 0 or start_h > 23 or end_h < 0 or end_h > 23:
                raise ValueError(f"窗口{i+1}: 小时必须在 0-23 之间")
            if start_m < 0 or start_m > 59 or end_m < 0 or end_m > 59:
                raise ValueError(f"窗口{i+1}: 分钟必须在 0-59 之间")

            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            if start_minutes >= end_minutes:
                raise ValueError(f"窗口{i+1}: 开始时间 {start} 必须在结束时间 {end} 之前")

    def get_time_windows(self):
        """获取所有时间窗口"""
        return self.time_windows

    def is_within_time_window(self):
        """检查当前时间是否在配置的时间窗口内"""
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        for window in self.time_windows:
            start = window.get('start', '09:00')
            end = window.get('end', '11:30')
            start_h, start_m = self._parse_time(start)
            end_h, end_m = self._parse_time(end)

            # 计算当前时间在窗口中的位置
            current_total_minutes = current_hour * 60 + current_minute
            start_total_minutes = start_h * 60 + start_m
            end_total_minutes = end_h * 60 + end_m

            if start_total_minutes <= current_total_minutes <= end_total_minutes:
                return True

        return False

    def generate_random_execution_time(self, window_index=0):
        """在指定时间窗口内生成随机执行时间点"""
        if window_index >= len(self.time_windows):
            window_index = 0

        window = self.time_windows[window_index]
        start = window.get('start', '09:00')
        end = window.get('end', '11:30')

        start_h, start_m = self._parse_time(start)
        end_h, end_m = self._parse_time(end)

        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        random_minutes = random.randint(start_minutes, end_minutes - 1)
        hours = random_minutes // 60
        minutes = random_minutes % 60

        now = datetime.now()
        # 生成今天的执行时间
        execution_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        # 如果已过时间，安排明天
        if execution_time <= now:
            execution_time += timedelta(days=1)

        return execution_time

    def is_weekend(self, dt):
        """检查是否周末（周六、周日）"""
        # TODO: 法定节假日检查（需要接入节假日API或数据库）
        return dt.weekday() >= 5  # 5=Saturday, 6=Sunday

    def get_time_window_hours(self):
        """获取所有时间窗口的小时范围列表"""
        hour_ranges = []
        for window in self.time_windows:
            start = window.get('start', '09:00')
            end = window.get('end', '11:30')
            start_h, _ = self._parse_time(start)
            end_h, _ = self._parse_time(end)
            hour_ranges.append((start_h, end_h))
        return hour_ranges

    def get_time_window_minutes(self):
        """获取所有时间窗口的分钟范围列表"""
        minute_ranges = []
        for window in self.time_windows:
            start = window.get('start', '09:00')
            end = window.get('end', '11:30')
            _, start_m = self._parse_time(start)
            _, end_m = self._parse_time(end)
            minute_ranges.append((start_m, end_m))
        return minute_ranges

    def get_next_run_time(self):
        """获取下一个可执行的时间点（跳过周末）"""
        candidate = self.generate_random_execution_time()

        # 跳过周末，直到找到工作日
        while self.is_weekend(candidate):
            candidate += timedelta(days=1)

        return candidate


class ExecutionLogger:
    """执行日志记录器"""

    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.db_path = os.path.join(log_dir, 'execution_log.db')
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planned_time TEXT,
                actual_time TEXT,
                target_app TEXT,
                device_serial TEXT,
                result TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def log_execution(self, planned_time, actual_time, target_app, device_serial,
                      result, error_message=None):
        """记录执行结果"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO execution_log
            (planned_time, actual_time, target_app, device_serial, result, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (planned_time, actual_time, target_app, device_serial, result, error_message))
        conn.commit()
        conn.close()

    def get_recent_logs(self, limit=10):
        """获取最近的执行记录"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT planned_time, actual_time, target_app, result, error_message, created_at
            FROM execution_log
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = c.fetchall()
        conn.close()
        return rows


class ScheduledAppLauncher:
    """定时启动 App 的执行器"""

    def __init__(self, config):
        self.config = config
        self.logger = ExecutionLogger(config.log_dir)
        self.device = None

    def connect_device(self):
        """连接设备，支持重试"""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                print(f"[Scheduler] 尝试连接设备 (尝试 {attempt}/{self.config.max_retries})...")
                self.device = ops.connect(self.config.device_serial)
                print(f"[Scheduler] 设备连接成功: {self.device.serial}")
                return True
            except Exception as e:
                print(f"[Scheduler] 连接失败: {e}")
                if attempt < self.config.max_retries:
                    print(f"[Scheduler] {self.config.retry_interval}秒后重试...")
                    time.sleep(self.config.retry_interval)
                else:
                    print(f"[Scheduler] 达到最大重试次数，放弃连接")
                    return False
        return False

    def verify_app_launched(self, package, timeout=5):
        """验证 App 是否成功启动"""
        if not self.device:
            return False
        try:
            time.sleep(timeout)
            current = ops.get_current_app(self.device)
            return current == package
        except Exception as e:
            print(f"[Scheduler] 验证失败: {e}")
            return False

    def execute_launch(self, planned_time):
        """执行 App 启动"""
        actual_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = "FAIL"
        error_msg = None

        try:
            # 连接设备
            if not self.connect_device():
                error_msg = "设备连接失败"
                raise Exception(error_msg)

            # 启动 App
            print(f"[Scheduler] 正在启动 App: {self.config.target_app}")
            ops.launch_app(self.device, self.config.target_app)

            # 验证
            if self.verify_app_launched(self.config.target_app):
                result = "SUCCESS"
                print(f"[Scheduler] App 启动验证成功")

                # 等待10秒后关闭 App
                print(f"[Scheduler] 等待10秒后关闭 App...")
                time.sleep(10)
                print(f"[Scheduler] 正在关闭 App: {self.config.target_app}")
                ops.stop_app(self.device, self.config.target_app)
                print(f"[Scheduler] App 已关闭")
            else:
                error_msg = "App 启动后验证失败"
                raise Exception(error_msg)

        except Exception as e:
            error_msg = str(e)
            print(f"[Scheduler] 执行失败: {error_msg}")

        finally:
            # 记录日志
            self.logger.log_execution(
                planned_time,
                actual_time,
                self.config.target_app,
                self.config.device_serial or "auto",
                result,
                error_msg
            )

            print(f"[Scheduler] 执行记录: 计划={planned_time}, 实际={actual_time}, 结果={result}")

        return result == "SUCCESS"

    def scheduled_job(self):
        """调度器执行的 job"""
        planned_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*50}")
        print(f"[Scheduler] 触发执行 | 计划时间: {planned_time}")

        if self.config.is_weekend(datetime.now()):
            print(f"[Scheduler] 跳过周末执行")
            return

        # 检查是否在时间窗口内
        if not self.config.is_within_time_window():
            print(f"[Scheduler] 当前不在时间窗口内，跳过执行")
            print(f"{'='*50}\n")
            return

        success = self.execute_launch(planned_time)
        print(f"[Scheduler] 执行{'成功' if success else '失败'}")
        print(f"{'='*50}\n")

    def print_status(self):
        """打印当前状态"""
        print("\n" + "="*50)
        print("定时任务状态")
        print("="*50)
        print(f"目标 App: {self.config.target_app}")
        print(f"设备序列号: {self.config.device_serial or '自动检测'}")

        window_descriptions = []
        for window in self.config.time_windows:
            window_descriptions.append(f"{window.get('start', '09:00')}~{window.get('end', '11:30')}")
        print(f"时间窗口: {', '.join(window_descriptions)}")
        print(f"最大重试: {self.config.max_retries} 次")
        print(f"重试间隔: {self.config.retry_interval} 秒")
        print(f"日志目录: {self.config.log_dir}")
        print("="*50)

        print("\n最近执行记录:")
        logs = self.logger.get_recent_logs(5)
        if logs:
            for log in logs:
                print(f"  {log[5]} | 计划:{log[0]} | 实际:{log[1]} | {log[2]} | {log[3]}")
                if log[4]:
                    print(f"    错误: {log[4]}")
        else:
            print("  暂无执行记录")

        print("\n最近 10 条日志文件: logs/show")
        print("="*50 + "\n")


def load_config(config_path='config/schedule_config.yaml'):
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    return ScheduleConfig(config_path)


def start_scheduler(config_path='config/schedule_config.yaml'):
    """启动调度器"""
    print("[Scheduler] 正在加载配置...")

    config = load_config(config_path)

    launcher = ScheduledAppLauncher(config)
    launcher.print_status()

    # 创建调度器，使用 SQLite 持久化任务
    db_path = os.path.join(config.log_dir, 'scheduler_jobs.db')
    jobstores = {
        'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
    }

    scheduler = BlockingScheduler(jobstores=jobstores)

    # 根据配置的多个时间窗口设置 CronTrigger
    hour_ranges = config.get_time_window_hours()

    # 构建小时列表：例如 [8,9,18,19]
    # 每个窗口会触发整点执行，实际窗口检查在 scheduled_job 中进行
    all_hours = []
    for start_h, end_h in hour_ranges:
        all_hours.extend(range(start_h, end_h + 1))

    # 去重并排序
    all_hours = sorted(set(all_hours))

    hours_str = ','.join(str(h) for h in all_hours)

    # 每小时整点触发，由 scheduled_job 中的 is_within_time_window() 检查实际窗口
    trigger = CronTrigger(day_of_week='mon-fri', hour=hours_str, minute=0)

    # 显示所有时间窗口
    window_descriptions = []
    for window in config.time_windows:
        window_descriptions.append(f"{window.get('start', '09:00')}~{window.get('end', '11:30')}")

    print(f"[Scheduler] 时间窗口: {', '.join(window_descriptions)}")
    print(f"[Scheduler] Cron trigger: 每小时整点触发 ({hours_str}:00)")

    scheduler.add_job(
        launcher.scheduled_job,
        trigger,
        id='scheduled_app_launch',
        name='定时启动 App',
        replace_existing=True
    )

    print("[Scheduler] 调度器已启动")
    print(f"[Scheduler] 执行周期: 周一到周五 {', '.join(window_descriptions)}")
    print("[Scheduler] 按 Ctrl+C 退出")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[Scheduler] 调度器已停止")
        scheduler.shutdown()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='AndroidAuto 定时任务调度器')
    parser.add_argument('--config', '-c', default='config/schedule_config.yaml',
                        help='配置文件路径 (默认: config/schedule_config.yaml)')
    parser.add_argument('--status', '-s', action='store_true',
                        help='查看调度状态和最近执行记录')

    args = parser.parse_args()

    if args.status:
        config = load_config(args.config)
        launcher = ScheduledAppLauncher(config)
        launcher.print_status()
    else:
        start_scheduler(args.config)


if __name__ == "__main__":
    main()