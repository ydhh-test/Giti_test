# -*- coding: utf-8 -*-

"""
纵图拼接类

实现多个输入目录的纵向图片拼接处理，包括：
- 图片纵向拼接
- 分辨率调整
- 批量处理

# Copyright © 2026. All rights reserved.
# Author: 桂禹
# AI Assistant: ClaudeCode (Claude Sonnet 4)
"""

from pathlib import Path
import shutil
from PIL import Image

from utils.logger import get_logger, LoggerMixin
from utils.exceptions import StitchingError, ImageLoadError, ImageSaveError


class VerticalStitch(LoggerMixin):
    """纵图拼接处理类"""

    def __init__(self, task_id: str, conf: dict):
        """
        初始化纵向拼接类

        Args:
            task_id: 任务ID
            conf: 配置字典，包含 base_path 和 filters
        """
        self.task_id = task_id
        self.conf = conf
        self.base_path = conf["base_path"]
        self.filters = conf["filters"]
        self.logger.info(f"初始化VerticalStitch: task_id={task_id}, base_path={self.base_path}")

    def process(self) -> tuple[bool, dict]:
        """
        主处理流程

        Returns:
            tuple[bool, dict]: (是否成功, 处理详情)
                details 格式:
                {
                    "center_filter": {
                        "success": ["path/to/1.png", ...],
                        "failed": ["path/to/2.png", ...],
                        "skipped": []
                    },
                    "side_filter": {
                        "success": [...],
                        "failed": [...],
                        "skipped": []
                    }
                }
        """
        try:
            self.logger.info(f"开始纵图拼接处理，task_id={self.task_id}")
            results = {}
            all_success = True

            for filter_config in self.filters:
                filter_dir = filter_config["dir"]
                try:
                    result = self._process_filter(filter_config)
                    results[filter_dir] = result

                    success_count = len(result["success"])
                    failed_count = len(result["failed"])
                    skipped_count = len(result["skipped"])

                    self.logger.info(
                        f"Filter {filter_dir} 处理完成: "
                        f"成功={success_count}, 失败={failed_count}, 跳过={skipped_count}"
                    )

                    if result["failed"]:
                        all_success = False

                except Exception as e:
                    self.logger.error(f"处理filter {filter_dir}时发生错误: {str(e)}")
                    results[filter_dir] = {"success": [], "failed": [], "skipped": []}
                    all_success = False

            return all_success, results

        except Exception as e:
            self.logger.error(f"纵图拼接处理失败: {str(e)}")
            raise StitchingError(f"处理失败: {str(e)}")

    def _process_filter(self, filter_config: dict) -> dict:
        """
        处理单个 filter 目录

        Args:
            filter_config: 单个 filter 的配置

        Returns:
            dict: 包含 success, failed, skipped 列表
        """
        filter_dir = filter_config["dir"]
        stitch_count = filter_config["stitch_count"]
        resolution = tuple(filter_config["resolution"])

        result = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        try:
            # 获取目录路径
            task_dir = self._get_task_dir()
            input_dir = task_dir / filter_dir

            # 从配置中获取输出目录后缀
            output_suffix = "_vertical"
            vertical_stitch_conf = self.conf.get('vertical_stitch_conf', {})
            if isinstance(vertical_stitch_conf, dict):
                output_suffix = vertical_stitch_conf.get('output_dir_suffix', '_vertical')
            output_dir = task_dir / f"{filter_dir.split('_')[0]}{output_suffix}"

            self.logger.debug(f"处理filter目录: {input_dir}")

            # 检查输入目录是否存在
            if not input_dir.exists():
                self.logger.warning(f"输入目录不存在，跳过: {input_dir}")
                result["skipped"].append(str(input_dir))
                return result

            # 检查是否为空目录
            if not any(input_dir.iterdir()):
                self.logger.warning(f"输入目录为空，跳过: {input_dir}")
                result["skipped"].append(str(input_dir))
                return result

            # 清空并重建输出目录
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            self.logger.debug(f"输出目录已创建: {output_dir}")

            # 从配置中获取支持的图像扩展名
            image_extensions = ['.png']
            postprocessor_conf = self.conf.get('postprocessor_conf', {})
            if isinstance(postprocessor_conf, dict):
                image_extensions = postprocessor_conf.get('supported_image_extensions', ['.png'])

            # 获取图片列表
            image_files = []
            for ext in image_extensions:
                image_files.extend(sorted(input_dir.glob(f"*{ext}"), key=lambda x: x.name))

            self.logger.debug(f"找到 {len(image_files)} 个图片文件")

            # 逐张处理图片
            for image_path in image_files:
                try:
                    success = self._stitch_and_resize(
                        image_path,
                        output_dir / image_path.name,
                        stitch_count,
                        resolution
                    )
                    if success:
                        result["success"].append(str(image_path))
                        self.logger.debug(f"成功处理图片: {image_path}")
                    else:
                        result["failed"].append(str(image_path))
                        self.logger.error(f"处理图片失败: {image_path}")
                except Exception as e:
                    result["failed"].append(str(image_path))
                    self.logger.error(f"处理图片时发生错误 {image_path}: {str(e)}")

        except Exception as e:
            self.logger.error(f"处理filter目录 {filter_dir} 时发生错误: {str(e)}")
            raise

        return result

    def _stitch_and_resize(
        self,
        input_path: Path,
        output_path: Path,
        stitch_count: int,
        target_size: tuple
    ) -> bool:
        """
        对单张图片进行纵向拼接和 resize

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            stitch_count: 拼接次数
            target_size: 目标尺寸 (width, height)

        Returns:
            bool: 是否处理成功

        Raises:
            ImageLoadError: 当图片加载失败时
            ImageSaveError: 当图片保存失败时
            StitchingError: 当拼接过程失败时
        """
        try:
            self.logger.debug(
                f"开始处理图片: {input_path}, "
                f"stitch_count={stitch_count}, target_size={target_size}"
            )

            # 读取原始图片
            try:
                img = Image.open(input_path)
                img_width, img_height = img.size
                self.logger.debug(f"原始图片尺寸: {img_width}x{img_height}")
            except Exception as e:
                raise ImageLoadError(str(input_path), f"PIL打开失败: {str(e)}")

            # 创建拼接后的图片画布
            try:
                stitched_width = img_width
                stitched_height = img_height * stitch_count
                stitched = Image.new("RGB", (stitched_width, stitched_height))

                # 纵向拼接
                for i in range(stitch_count):
                    stitched.paste(img, (0, i * img_height))

                self.logger.debug(f"拼接完成，尺寸: {stitched_width}x{stitched_height}")

            except Exception as e:
                raise StitchingError(f"纵向拼接失败: {str(e)}")

            # Resize 到目标尺寸
            try:
                resized = stitched.resize(target_size, Image.LANCZOS)
                self.logger.debug(f"调整尺寸完成: {target_size}")
            except Exception as e:
                raise StitchingError(f"调整尺寸失败: {str(e)}")

            # 保存图片
            try:
                resized.save(output_path, "PNG")
                self.logger.debug(f"图片保存成功: {output_path}")
            except Exception as e:
                raise ImageSaveError(str(output_path), f"PIL保存失败: {str(e)}")

            return True

        except (ImageLoadError, ImageSaveError, StitchingError):
            # 重新抛出我们自定义的异常
            raise
        except Exception as e:
            # 捕获其他异常并转换为StitchingError
            self.logger.error(f"处理图片时发生未知错误: {input_path}, 错误: {str(e)}")
            raise StitchingError(f"未知错误: {str(e)}")

    def _get_task_dir(self) -> Path:
        """
        获取 task_id 目录路径

        Returns:
            Path: task_id 目录路径
        """
        return Path(self.base_path) / f"task_id_{self.task_id}"
