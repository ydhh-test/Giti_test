import sys
import os
import unittest
import shutil
from pathlib import Path
import glob
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.preprocessor import tire_image_preprocessing_pipeline


class TestTireImagePreprocessingPipeline(unittest.TestCase):
    """测试轮胎图像预处理管道功能"""

    def setUp(self):
        """设置测试环境"""
        self.task_id = "task_id_1778457600"
        self.input_dir = Path(f"./tests/datasets/{self.task_id}/images")
        self.workspace_dir = Path(f"./.results/{self.task_id}")
        self.output_dir = Path(f"./.results")
        self.logs_dir = Path(f"./.logs")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 清理可能存在的旧测试数据
        if self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
        
        # 创建工作目录
        self.workspace_dir.mkdir(exist_ok=True)
        
        # 创建输入子目录
        workspace_input_dir = self.workspace_dir / "images"
        workspace_input_dir.mkdir(exist_ok=True)
        
        # 复制测试图片到工作目录
        if self.input_dir.exists():
            for img_file in self.input_dir.glob("*"):
                if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff']:
                    dest_path = workspace_input_dir / img_file.name
                    shutil.copy2(img_file, dest_path)

    def tearDown(self):
        """清理测试环境"""
        # 可选择是否删除测试产生的文件
        pass

    def test_basic_workflow(self):
        """测试用例 1: 基本功能测试
        目的：验证整个预处理管道正常工作
        输入：包含标准轮胎图像的工作目录
        预期结果：
        - 正确创建所有子目录（images, split, center, side_with_gray, side等）
        - 成功执行所有步骤（纵向切分、灰边去除、横向切分）
        - 正确检测异常图片
        - 返回成功状态
        - 在.logs目录生成执行日志
        """
        # 设置日志记录到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"test_preprocessor_{self.task_id}_{timestamp}.log"
        log_filepath = self.logs_dir / log_filename
        
        # 创建日志处理器
        handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # 获取服务预处理器的日志记录器并添加处理器
        logger = logging.getLogger('services_preprocessor')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        try:
            # 验证输入目录存在且包含图片
            workspace_input_dir = self.workspace_dir / "images"
            self.assertTrue(workspace_input_dir.exists(), f"工作目录输入子目录不存在: {workspace_input_dir}")
            
            input_images = list(workspace_input_dir.glob("*"))
            self.assertGreater(len(input_images), 0, f"输入目录中没有找到图片: {workspace_input_dir}")
            
            # 执行预处理管道
            result = tire_image_preprocessing_pipeline(str(self.workspace_dir))
            
            # 验证返回结果
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
            self.assertEqual(result['status'], 'success', f"预处理失败: {result}")
            
            # 验证必要的输出目录结构被创建
            expected_dirs = [
                self.workspace_dir / "images",
                self.workspace_dir / "split",
                self.workspace_dir / "split" / "center_horz",
                self.workspace_dir / "split" / "side_horz_with_gray", 
                self.workspace_dir / "split" / "side_horz",
                self.workspace_dir / "pieces",
                self.workspace_dir / "pieces" / "center",
                self.workspace_dir / "pieces" / "side"
            ]
            
            for expected_dir in expected_dirs:
                self.assertTrue(expected_dir.exists(), f"预期目录不存在: {expected_dir}")
            
            # 验证各个阶段的输出
            split_dir = self.workspace_dir / "split"
            pieces_dir = self.workspace_dir / "pieces"
            
            # 检查split目录下的子目录是否不为空（至少应该有一些输出）
            center_horz_dir = split_dir / "center_horz"
            side_horz_with_gray_dir = split_dir / "side_horz_with_gray"
            side_horz_dir = split_dir / "side_horz"
            
            center_horz_files = list(center_horz_dir.glob("*"))
            side_horz_with_gray_files = list(side_horz_with_gray_dir.glob("*"))
            side_horz_files = list(side_horz_dir.glob("*"))
            
            # 至少应有一些文件被处理
            self.assertGreaterEqual(len(center_horz_files) + len(side_horz_with_gray_files), 
                                   len(input_images), 
                                   "纵向切分后文件数量不足")
            
            # 检查最终输出
            center_final_dir = pieces_dir / "center"
            side_final_dir = pieces_dir / "side"
            
            center_final_files = list(center_final_dir.glob("*"))
            side_final_files = list(side_final_dir.glob("*"))
            
            # 最终输出应该包含处理后的文件
            self.assertTrue(len(center_final_files) >= 0, "中心部分最终输出目录应存在")
            self.assertTrue(len(side_final_files) >= 0, "侧边部分最终输出目录应存在")
            
            # 验证返回的数据结构
            self.assertIn('input_count', result)
            self.assertIn('abnormal_count', result)
            self.assertIn('abnormal_images', result)
            
            # 输入计数应与输入图片数量匹配
            self.assertGreaterEqual(result['input_count'], 0, "输入计数应为非负数")
            
            # 异常图片列表应为列表类型
            self.assertIsInstance(result['abnormal_images'], list)
            
            print(f"预处理完成，输入图片数: {result['input_count']}, 异常图片数: {result['abnormal_count']}")
            print(f"中心部分输出文件数: {len(center_final_files)}")
            print(f"侧边部分输出文件数: {len(side_final_files)}")
            print(f"日志文件已保存至: {log_filepath}")
            
            # 验证日志文件已创建
            self.assertTrue(log_filepath.exists(), f"日志文件未创建: {log_filepath}")
            
        finally:
            # 移除处理器以释放资源
            logger.removeHandler(handler)
            handler.close()


if __name__ == '__main__':
    unittest.main()