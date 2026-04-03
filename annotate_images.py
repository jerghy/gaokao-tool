import argparse
from ai.image_annotator import scan_unannotated_configs, batch_annotate_images


def main():
    parser = argparse.ArgumentParser(
        description="AI图片标注工具 - 自动为图片生成 charBox 和 splitLines 标注",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", "--images-json",
        type=str,
        default="images.json",
        help="images.json 文件路径 (默认: images.json)",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=3,
        help="并发数 (默认: 3)",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="不跳过已标注的配置",
    )
    parser.add_argument(
        "--no-charbox",
        action="store_true",
        help="不标注 charBox",
    )
    parser.add_argument(
        "--no-splitlines",
        action="store_true",
        help="不标注 splitLines",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="只扫描不标注",
    )

    args = parser.parse_args()

    if args.scan_only:
        unannotated = scan_unannotated_configs(args.images_json)
        print(f"未标注的配置数量: {len(unannotated)}")
        if unannotated:
            print("\n未标注的配置列表:")
            for item in unannotated[:20]:
                print(f"  - {item['config_id']}")
            if len(unannotated) > 20:
                print(f"  ... 还有 {len(unannotated) - 20} 个")
    else:
        batch_annotate_images(
            images_json_path=args.images_json,
            max_workers=args.workers,
            skip_existing=not args.no_skip,
            annotate_charbox=not args.no_charbox,
            annotate_splitlines=not args.no_splitlines,
        )


if __name__ == "__main__":
    main()
