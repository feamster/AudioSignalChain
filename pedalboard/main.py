# main.py
import argparse
from effects_processor import EffectsProcessor
from effects_presets import get_effect_presets, get_individual_effects


def main():
    parser = argparse.ArgumentParser(description="Guitar Effects Processor")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Launch the Gradio GUI")

    # Process file command
    process_parser = subparsers.add_parser("process", help="Process an audio file")
    process_parser.add_argument("input_file", help="Input audio file to process")
    process_parser.add_argument("output_file", help="Output audio file")
    process_parser.add_argument("--preset", help="Effect preset to use", choices=get_effect_presets().keys())

    # Real-time processing command
    realtime_parser = subparsers.add_parser("realtime", help="Start real-time processing")
    realtime_parser.add_argument("--preset", help="Effect preset to use", choices=get_effect_presets().keys())
    realtime_parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate (default: 44100)")
    realtime_parser.add_argument("--block-size", type=int, default=512, help="Block size (default: 512)")

    # List presets command
    subparsers.add_parser("list-presets", help="List available effect presets")

    # List effects command
    subparsers.add_parser("list-effects", help="List available individual effects")

    args = parser.parse_args()

    if args.command == "gui":
        # Import here to avoid importing Gradio when not needed
        from app import app
        app.launch()

    elif args.command == "process":
        processor = EffectsProcessor()

        if args.preset:
            presets = get_effect_presets()
            if args.preset in presets:
                preset_board = presets[args.preset]()
                for effect in preset_board:
                    processor.add_effect(effect)
                print(f"Applied {args.preset} preset with {len(preset_board)} effects")

        processor.process_file(args.input_file, args.output_file)
        print(f"Processed {args.input_file} -> {args.output_file}")

    elif args.command == "realtime":
        processor = EffectsProcessor(
            sample_rate=args.sample_rate,
            block_size=args.block_size,
            channels=1
        )

        if args.preset:
            presets = get_effect_presets()
            if args.preset in presets:
                preset_board = presets[args.preset]()
                for effect in preset_board:
                    processor.add_effect(effect)
                print(f"Applied {args.preset} preset with {len(preset_board)} effects")

        print("Starting real-time processing. Press Ctrl+C to stop.")
        processor.start()

        try:
            # Keep the program running until interrupted
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            processor.stop()
            print("Stopped real-time processing")

    elif args.command == "list-presets":
        presets = get_effect_presets()
        print("Available Effect Presets:")
        for name in presets.keys():
            print(f"- {name}")

    elif args.command == "list-effects":
        effects = get_individual_effects()
        print("Available Individual Effects:")
        for name in effects.keys():
            print(f"- {name}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()