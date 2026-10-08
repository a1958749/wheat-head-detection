from __future__ import annotations

from datetime import datetime

from app.models import RuntimeState, RuntimeStatus


STATUS_TEXT = {
    RuntimeStatus.IDLE: "空闲",
    RuntimeStatus.READY: "就绪",
    RuntimeStatus.RUNNING: "运行中",
    RuntimeStatus.PAUSED: "已暂停",
    RuntimeStatus.FINISHED: "已完成",
    RuntimeStatus.ERROR: "异常",
}


class RuntimeStateManager:
    def __init__(self):
        self.state = RuntimeState()

    def update(self, **kwargs) -> RuntimeState:
        for key, value in kwargs.items():
            setattr(self.state, key, value)
        self.state.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.state

    def set_idle(self, message: str = "系统空闲") -> RuntimeState:
        return self.update(
            status=RuntimeStatus.IDLE,
            message=message,
            error_message="",
            progress_current=0,
            progress_total=0,
            progress_text="0 / 0",
            current_fps=0.0,
        )

    def set_ready(self, source_type: str = "", source_name: str = "", source_path: str = "", message: str = "已准备就绪") -> RuntimeState:
        return self.update(
            status=RuntimeStatus.READY,
            source_type=source_type,
            source_name=source_name,
            source_path=source_path,
            current_file_name=source_name,
            message=message,
            error_message="",
        )

    def set_running(
        self,
        source_type: str,
        source_name: str,
        source_path: str,
        current_file_name: str,
        progress_current: int,
        progress_total: int,
        message: str,
        current_fps: float = 0.0,
    ) -> RuntimeState:
        total = max(progress_total, 0)
        current = max(progress_current, 0)
        return self.update(
            status=RuntimeStatus.RUNNING,
            source_type=source_type,
            source_name=source_name,
            source_path=source_path,
            current_file_name=current_file_name,
            progress_current=current,
            progress_total=total,
            progress_text=f"{current} / {total}" if total else "-",
            message=message,
            current_fps=current_fps,
            error_message="",
        )

    def set_paused(self, message: str = "任务已暂停") -> RuntimeState:
        return self.update(status=RuntimeStatus.PAUSED, message=message)

    def set_finished(self, message: str = "任务已完成") -> RuntimeState:
        return self.update(status=RuntimeStatus.FINISHED, message=message, error_message="")

    def set_error(self, message: str, error_message: str = "") -> RuntimeState:
        return self.update(status=RuntimeStatus.ERROR, message=message, error_message=error_message or message)

    @staticmethod
    def status_text(status: RuntimeStatus) -> str:
        return STATUS_TEXT.get(status, "未知")
