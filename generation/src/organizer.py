from pathlib import Path
import pandas as pd
import numpy as np
import random
from typing import Union, List, Optional
from openai import OpenAI
import time
from concurrent.futures import ThreadPoolExecutor
import os

from pathlib import Path
import pandas as pd
import numpy as np
import random
from typing import Union, List, Optional, Set
from openai import OpenAI
import time
from concurrent.futures import ThreadPoolExecutor
import os
import resource

# Increase the file descriptor limit for this process
# This is a key fix for your "Too many open files" error
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
print(f"File descriptor limits: soft={soft}, hard={hard}, now set to {hard}")

class AudioGenerator:
    """Handles audio generation for a dataset of sentences."""
    
    def __init__(self, output_dir='stim', openai_key=None):
        """
        Initialize the audio generator.
        
        Args:
            output_dir: Directory to save audio files
            openai_key: OpenAI API key for TTS
        """
        self.output_dir = Path(output_dir)
        self.audio_dir = self.output_dir / 'audio'
        self.openai_key = openai_key
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache the existing files to avoid repeated disk checks
        self._existing_files = self._cache_existing_files()
        print(f"Found {len(self._existing_files)} existing audio files")
    
    def _cache_existing_files(self) -> Set[str]:
        """Cache all existing files to avoid repeated disk checks"""
        return {f.name for f in self.audio_dir.glob("*.wav")}
    
    def generate_speech(self, row, voice: str = "alloy", model: str = "tts-1") -> Optional[Path]:
        """Generate speech for a single sentence using its audio_filename"""
        if self.openai_key is None:
            raise ValueError("OpenAI API key is required for speech generation")
        
        speech_file_path = self.audio_dir / row['audio_filename']
        
        # Check cached files instead of disk access
        if row['audio_filename'] in self._existing_files:
            return speech_file_path
        
        client = None
        try:
            # Create a new client for each request to avoid connection pooling issues
            client = OpenAI(api_key=self.openai_key)
            
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=row['sentence']
            )
            
            # Use a context manager for file handling to ensure proper closure
            with open(str(speech_file_path), 'wb') as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)
            
            # Add to cache
            self._existing_files.add(row['audio_filename'])
            print(f"Generated: {speech_file_path}")
            return speech_file_path
            
        except Exception as e:
            print(f"Error generating audio for: {row['sentence']}\nError: {str(e)}")
            return None
    
    def generate_audio_for_dataset(self, df, max_workers=3, batch_size=10, delay_between_batches=1):
        """
        Generate speech for all sentences in a dataframe.
        
        Args:
            df: DataFrame containing sentences and audio_filename columns
            max_workers: Maximum number of parallel workers (reduced from 5 to 3)
            batch_size: Number of requests to process in each batch (reduced from 20 to 10)
            delay_between_batches: Delay in seconds between batches (increased from 0 to 1)
            
        Returns:
            List of generated file paths or None for failed generations
        """
        if 'sentence' not in df.columns or 'audio_filename' not in df.columns:
            raise ValueError("DataFrame must contain 'sentence' and 'audio_filename' columns")
        
        # Filter out sentences that already have audio files
        existing_files = self._existing_files
        df_to_process = df[~df['audio_filename'].isin(existing_files)].copy()
        
        print(f"Skipping {len(df) - len(df_to_process)} already generated files")
        print(f"Processing {len(df_to_process)} remaining sentences")
        
        if len(df_to_process) == 0:
            print("All files already exist. Nothing to process.")
            return [self.audio_dir / filename for filename in df['audio_filename']]
        
        def process_batch(rows):
            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.generate_speech, row) for row in rows]
                for future in futures:
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"Error in batch processing: {str(e)}")
                        results.append(None)
            return results

        # Split the dataframe into batches
        total_rows = len(df_to_process)
        batches = [df_to_process[i:i + batch_size] for i in range(0, total_rows, batch_size)]
        
        print(f"Processing {total_rows} sentences in {len(batches)} batches of {batch_size}")
        
        all_results = []
        for i, batch in enumerate(batches, 1):
            print(f"\nProcessing batch {i}/{len(batches)}")
            
            # Add exponential backoff if errors occur
            retries = 0
            max_retries = 3
            batch_results = None
            
            while retries <= max_retries:
                try:
                    batch_results = process_batch(batch.to_dict('records'))
                    break
                except Exception as e:
                    retries += 1
                    wait_time = 2 ** retries  # Exponential backoff
                    print(f"Batch error, retrying in {wait_time}s ({retries}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
            
            if batch_results:
                all_results.extend(batch_results)
            
            if i < len(batches):  # Don't delay after the last batch
                print(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)
        
        # Add already existing files to results
        existing_results = [self.audio_dir / filename for filename in df['audio_filename'] 
                           if filename in existing_files]
        all_results.extend(existing_results)
        
        # Count successes and failures
        successes = sum(1 for r in all_results if r is not None)
        failures = sum(1 for r in all_results if r is None)
        
        print(f"\nGeneration complete:")
        print(f"Successful generations: {successes}")
        print(f"Failed generations: {failures}")
        
        return all_results

class DatasetPreparator:
    def __init__(self):
        """Initialize the dataset preparator."""
        pass
    
    def prepare_controlled_data(self, df):
        """
        Prepare controlled dataset with proper columns and audio filename.
        
        Args:
            df: DataFrame containing controlled stimuli
            
        Returns:
            Processed DataFrame
        """
        df = df.copy()
        df['dataset'] = 'controlled'
        
        # Preserve the structure column
        if 'structure' not in df.columns:
            df['structure'] = None
            
        # Rename word_count to num_words if it exists
        if 'word_count' in df.columns and 'num_words' not in df.columns:
            df.rename(columns={'word_count': 'num_words'}, inplace=True)
        
        # Create sentence_id for reference
        df['sentence_id'] = [f"ctrl_{i:05d}" for i in range(len(df))]
        
        # Create audio filename
        df['audio_filename'] = df['sentence_id'].apply(lambda x: f"{x}.wav")
        
        return df

    def prepare_naturalistic_data(self, df):
        """
        Prepare naturalistic dataset with sentence_id and audio filename.
        
        Args:
            df: DataFrame containing naturalistic stimuli
            
        Returns:
            Processed DataFrame
        """
        df = df.copy()
        df['dataset'] = 'naturalistic'
        
        # Handle numerosity column
        if 'numer' in df.columns and 'numerosity' not in df.columns:
            df['numerosity'] = df['numer']
            df.drop('numer', axis=1, inplace=True)
        
        # Handle word count columns
        if 'word_count' in df.columns and 'num_words' not in df.columns:
            df.rename(columns={'word_count': 'num_words'}, inplace=True)
        
        df['sentence_id'] = [f"nat_{i:05d}" for i in range(len(df))]
        df['audio_filename'] = df['sentence_id'].apply(lambda x: f"{x}.wav")
        
        return df

class RunOrganizer:
    def __init__(self, naturalistic_df=None, controlled_df=None, audio_dir='stim/audio', trials_per_run=80):
        """
        Initialize the run organizer.
        
        Args:
            naturalistic_df: Processed naturalistic DataFrame
            controlled_df: Processed controlled DataFrame
            audio_dir: Directory containing audio files
            trials_per_run: Number of trials in each run
        """
        self.naturalistic_df = naturalistic_df
        self.controlled_df = controlled_df
        self.trials_per_run = trials_per_run
        self.audio_dir = Path(audio_dir)
        
        # Combine dataframes if both are provided
        if naturalistic_df is not None and controlled_df is not None:
            # Ensure columns match before concatenation
            common_columns = set(naturalistic_df.columns) & set(controlled_df.columns)
            self.naturalistic_df = naturalistic_df[list(common_columns)]
            self.controlled_df = controlled_df[list(common_columns)]
            
            # Create a combined DataFrame
            self.combined_df = pd.concat(
                [self.naturalistic_df, self.controlled_df], 
                ignore_index=True
            )
        elif naturalistic_df is not None:
            self.combined_df = naturalistic_df
        elif controlled_df is not None:
            self.combined_df = controlled_df
        else:
            raise ValueError("At least one DataFrame must be provided")
    
    def verify_audio_files(self):
        """
        Verify that all audio files exist.
        
        Returns:
            Tuple of (missing_files, total_files)
        """
        missing_files = []
        
        for filename in self.combined_df['audio_filename']:
            file_path = self.audio_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        return missing_files, len(self.combined_df)
    
    def create_runs_for_subject(self, subject_id, n_runs=None):
        """
        Create runs for a single subject.
        
        Args:
            subject_id: Subject identifier
            n_runs: Number of runs to create (calculated automatically if None)
            
        Returns:
            DataFrame containing run information for the subject
        """
        # Get naturalistic and controlled files
        if self.naturalistic_df is not None:
            naturalistic_files = self.naturalistic_df['audio_filename'].tolist()
        else:
            naturalistic_files = []
            
        if self.controlled_df is not None:
            controlled_files = self.controlled_df['audio_filename'].tolist()
        else:
            controlled_files = []
        
        # Create word count mapping
        word_counts = dict(zip(self.combined_df['audio_filename'], self.combined_df['num_words']))
        
        # Calculate number of runs
        if n_runs is None:
            total_sentences = len(naturalistic_files) + len(controlled_files)
            n_runs = total_sentences // self.trials_per_run
        
        subject_runs = []
        
        # Shuffle sentences for this subject (each subject gets unique naturalistic sentences)
        random.shuffle(naturalistic_files)
        random.shuffle(controlled_files)
        
        # Create pools of files that we'll draw from for each run
        remaining_naturalistic = naturalistic_files.copy()
        remaining_controlled = controlled_files.copy()
        
        for run in range(1, n_runs + 1):
            run_sentences = []
            
            # Ensure we have enough naturalistic sentences for the start
            if len(remaining_naturalistic) < 3:
                print(f"Warning: Not enough naturalistic sentences for run {run}, using available ones")
                start_sentences = remaining_naturalistic.copy()
                run_sentences.extend(start_sentences)
                remaining_naturalistic = []
            else:
                # Start with 3 random naturalistic sentences
                start_sentences = random.sample(remaining_naturalistic, 3)
                run_sentences.extend(start_sentences)
                for sent in start_sentences:
                    remaining_naturalistic.remove(sent)
            
            # Pool for remaining sentences
            available_naturalistic = remaining_naturalistic.copy()
            available_controlled = remaining_controlled.copy()
            
            # Fill the rest of the run
            remaining_needed = self.trials_per_run - len(run_sentences)
            
            # Select remaining sentences avoiding consecutive long sentences
            while len(run_sentences) < self.trials_per_run:
                # Determine which pool to draw from
                if not available_naturalistic and not available_controlled:
                    print(f"Warning: Ran out of sentences for run {run}, recycling used sentences")
                    # If we've used all sentences, recycle some
                    if remaining_naturalistic:
                        available_naturalistic = remaining_naturalistic.copy()
                    if remaining_controlled:
                        available_controlled = remaining_controlled.copy()
                
                # Combine available sentences
                available_pool = available_naturalistic + available_controlled
                
                # Find candidates avoiding consecutive long sentences
                candidates = [s for s in available_pool 
                          if not (len(run_sentences) > 0 and 
                                word_counts.get(run_sentences[-1], 0) > 10 and 
                                word_counts.get(s, 0) > 10)]
                
                if not candidates:
                    candidates = available_pool
                    
                selected = random.choice(candidates)
                run_sentences.append(selected)
                
                # Remove from the appropriate pool
                if selected in available_naturalistic:
                    available_naturalistic.remove(selected)
                    remaining_naturalistic.remove(selected)
                elif selected in available_controlled:
                    available_controlled.remove(selected)
                    remaining_controlled.remove(selected)
            
            # Create run data
            for trial, sentence in enumerate(run_sentences, 1):
                subject_runs.append({
                    'subject': subject_id,
                    'run': run,
                    'trial': trial,
                    'audio_filename': sentence,
                    'is_naturalistic': sentence.startswith('nat_'),
                    'num_words': word_counts.get(sentence, None)
                })
        
        return pd.DataFrame(subject_runs)
    
    def create_runs_for_all_subjects(self, n_subjects, sentences_per_subject=None):
        """
        Create runs for multiple subjects.
        
        Args:
            n_subjects: Number of subjects
            sentences_per_subject: Number of sentences per subject (default: all available)
            
        Returns:
            DataFrame containing run information for all subjects
        """
        # First, verify that audio files exist
        missing_files, total_files = self.verify_audio_files()
        if missing_files:
            print(f"Warning: {len(missing_files)} audio files are missing out of {total_files}")
            print(f"First 5 missing files: {missing_files[:5]}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                raise FileNotFoundError(f"{len(missing_files)} audio files are missing")
        
        # If using the large naturalistic dataset (20K sentences),
        # each subject gets unique naturalistic sentences
        nat_sentences_available = len(self.naturalistic_df) if self.naturalistic_df is not None else 0
        ctrl_sentences_available = len(self.controlled_df) if self.controlled_df is not None else 0
        
        print(f"Available sentences: {nat_sentences_available} naturalistic, {ctrl_sentences_available} controlled")
        
        all_runs = []
        
        for subject in range(1, n_subjects + 1):
            print(f"Creating runs for subject {subject}/{n_subjects}")
            
            # For large naturalistic datasets, each subject gets unique sentences
            if nat_sentences_available > 5000:  # Arbitrary threshold for "large" dataset
                # Select a subset of naturalistic sentences for this subject
                nat_per_subject = nat_sentences_available // n_subjects
                nat_start_idx = (subject - 1) * nat_per_subject
                nat_end_idx = subject * nat_per_subject if subject < n_subjects else nat_sentences_available
                
                subject_nat_df = self.naturalistic_df.iloc[nat_start_idx:nat_end_idx].copy()
                
                # Create temporary run organizer with this subject's data
                subject_organizer = RunOrganizer(
                    naturalistic_df=subject_nat_df,
                    controlled_df=self.controlled_df,
                    audio_dir=self.audio_dir,
                    trials_per_run=self.trials_per_run
                )
                subject_runs = subject_organizer.create_runs_for_subject(subject)
            else:
                # Normal case: all subjects get the same pool of sentences
                subject_runs = self.create_runs_for_subject(subject)
            
            all_runs.append(subject_runs)
        
        return pd.concat(all_runs, ignore_index=True)


# Add these imports to your organizer.py file
import soundfile as sf
from tqdm import tqdm
import scipy.io.wavfile

class AudioMixer:
    """Handles audio mixing and click track generation for experiment stimuli."""
    
    def __init__(self, click_file: Path):
        self.click_file = Path(click_file)
        if not self.click_file.exists():
            raise FileNotFoundError(f"Click file not found: {click_file}")

    @staticmethod
    def load_sound(filename: Path) -> tuple:
        """Load audio file and return sample rate and data."""
        try:
            # Use soundfile instead of scipy.io.wavfile
            data, sample_rate = sf.read(filename, dtype='int16')
            # Ensure mono
            if len(data.shape) > 1:
                data = data[:, 0]  # Take first channel if stereo
            return sample_rate, data
        except Exception as e:
            raise ValueError(f"Could not load audio file: {e}")

    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to int16 range."""
        if audio_data.dtype != np.int16:
            audio_float = audio_data.astype(np.float32)
            max_val = np.max(np.abs(audio_float))
            if max_val > 0:
                audio_float = audio_float * (32767 / max_val)
            return audio_float.astype(np.int16)
        return audio_data

    @staticmethod
    def write_sound(filename: Path, sample_rate: int, audio_data: np.ndarray) -> None:
        """Write audio data to file with proper normalization."""
        normalized_data = AudioMixer.normalize_audio(audio_data)
        sf.write(filename, normalized_data.T, sample_rate, subtype='PCM_16')

    def mix_sound(self, target: np.ndarray, mix: np.ndarray, 
                position: float, sample_rate: int = 22050, 
                replace: bool = True) -> None:
        """Mix sound at specific position in target."""
        start = int(sample_rate * position)
        end = start + len(mix)
        
        # Trim mix if it would exceed target length
        if end > len(target):
            mix = mix[:len(target) - start]
            end = len(target)
        
        if replace:
            target[start:end] = mix
        else:
            target[start:end] += mix

    def generate_click_train(self, channel: np.ndarray, 
                        positions: List[float], sample_rate: int) -> np.ndarray:
        """Generate click train for given positions."""
        if len(channel.shape) != 1:
            raise ValueError("Input channel must be mono")
            
        # Create a channel the same length as input
        channel2 = np.zeros(len(channel))
        click_sr, click = self.load_sound(self.click_file)
        
        # Ensure click doesn't exceed the end of the audio
        if positions[-1] * sample_rate + len(click) > len(channel):
            positions[-1] = (len(channel) - len(click)) / sample_rate
        
        self.multi_mix(channel2, click, positions, sample_rate=sample_rate)
        return channel2

    def process_file(self, input_file: Path, output_file: Path) -> None:
        """Process audio file with normalization and add clicks at start and end."""
        try:
            sample_rate, channel1 = self.load_sound(input_file)
            channel1 = self.normalize_audio(channel1)
            
            # Calculate the end position in seconds, leaving room for the click
            click_sr, click = self.load_sound(self.click_file)
            end_position = (len(channel1) - len(click)) / sample_rate
            
            # Generate click train with clicks at start and end
            channel2 = self.generate_click_train(channel1, [0.0, end_position], sample_rate)
            
            # Create stereo sound with audio and clicks
            stereo_sound = np.vstack([channel1, channel2])
            
            self.write_sound(output_file, sample_rate, stereo_sound)
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
            
    def multi_mix(self, target: np.ndarray, mix: np.ndarray, 
                 positions: List[float], sample_rate: int = 22050, 
                 replace: bool = True) -> None:
        """Mix sound at multiple positions."""
        for pos in positions:
            self.mix_sound(target, mix, pos, sample_rate, replace)

    def process_directory(self, input_dir: Path, output_dir: Path):
        """Process all audio files in directory."""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        total = len(list(input_dir.glob('*.wav')))
        
        files = list(input_dir.glob('*.wav'))
        for audio_file in tqdm(files, desc="Processing audio files", unit="file"):
            try:
                output_file = output_dir / f"{audio_file.stem}_click.wav"
                self.process_file(audio_file, output_file)
                count += 1
                if count % 100 == 0:
                    print(f"Processed: {count}/{total} files")
            except Exception as e:
                print(f"Error processing {audio_file}: {e}")
                
        print(f"Successfully processed {count}/{total} files")