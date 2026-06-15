"""因子基类定义 - 第3章引入"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseFactor(ABC):
    """所有因子的基类"""

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算因子值，返回股票-因子值映射"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """返回因子名称"""
        pass

    @abstractmethod
    def get_direction(self) -> int:
        """因子方向：1=因子值越大越好，-1=越小越好"""
        pass
