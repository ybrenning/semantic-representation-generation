from src.organizer import DatasetPreparator
from src.organizer import AudioGenerator
from src.organizer import RunOrganizer
from src.organizer import AudioMixer
import pandas as pd
from pathlib import Path
from ..config import OPENAI_API_KEY


def main():
    # Example usage
    prep = DatasetPreparator()
    
    # Load and prepare datasets

    base_path = Path("/home/co/git/neurospin-new-protocol/")
    naturalistic_df = pd.read_csv(base_path / "stim/sentences/V2/processed/natural_two_passes_fixed.csv")
    # controlled_df = pd.read_csv(base_path / "stim/sentences/V2/processed/controlled_augmented.csv")
    
    processed_nat = prep.prepare_naturalistic_data(naturalistic_df)
    # processed_ctrl = prep.prepare_controlled_data(controlled_df)
    
    # Generate audio (can be done separately for each dataset)
    generator = AudioGenerator(openai_key=OPENAI_API_KEY)
    
    # Generate naturalistic audio
    generator.generate_audio_for_dataset(
        processed_nat, 
        max_workers=100, 
        batch_size=1000, 
        delay_between_batches=0
    )
    
    # Generate controlled audio
    generator.generate_audio_for_dataset(
        processed_ctrl, 
        max_workers=50, 
        batch_size=200, 
        delay_between_batches=0
    )
    
    # Create runs for all subjects
    organizer = RunOrganizer(
        naturalistic_df=processed_nat,
        controlled_df=processed_ctrl,
        audio_dir=base_path / "stim/audio",
        trials_per_run=80
    )
    
    # Verify audio files exist
    missing_files, total_files = organizer.verify_audio_files()
    print(f"Missing audio files: {len(missing_files)} out of {total_files}")
    
    # Create runs for 10 subjects
    runs_df = organizer.create_runs_for_all_subjects(n_subjects=10)
    
    # Save the runs to CSV
    runs_df.to_csv(base_path / "subject_runs.csv", index=False)
    
    print(f"Created runs for {runs_df['subject'].nunique()} subjects")
    print(f"Total trials: {len(runs_df)}")
    
    # Add click tracks to audio files
    print("\nGenerating audio files with clicks...")
    click_file = Path(base_path / "stim/test_clic/click.wav")
    audio_dir = Path(base_path / "stim/audio")
    click_audio_dir = Path(base_path / "stim/audio_with_clicks")
    
    # Check if click file exists
    if not click_file.exists():
        print(f"Warning: Click file not found at {click_file}")
        print("Please ensure the click file exists before running this step.")
    else:
        # Process all audio files to add clicks
        mixer = AudioMixer(click_file)
        mixer.process_directory(audio_dir, click_audio_dir)


if __name__ == "__main__":
    main()
