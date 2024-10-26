import mido

def parse_midi_file(file_name):
    midi_data = mido.MidiFile(file_name)
    notes_info = []
    
    # Set default tempo (120 BPM) in case there are no tempo changes
    tempo = 500000  # Default tempo in microseconds per beat
    ticks_per_beat = midi_data.ticks_per_beat
    microseconds_per_tick = tempo / ticks_per_beat
    
    for track in midi_data.tracks:
        current_time = 0  # Track the current time in the song
        for msg in track:
            current_time += msg.time * microseconds_per_tick / 1e6  # Convert ticks to real time (seconds)

            if msg.type == 'set_tempo':
                # Adjust tempo if there's a tempo change event
                tempo = msg.tempo
                microseconds_per_tick = tempo / ticks_per_beat

            elif msg.type == 'note_on' and msg.velocity > 0:
                # Add note information to the list
                notes_info.append({
                    'type': 'note_on',
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'time': current_time  # Time in seconds when the note is played
                })

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Add note off information
                notes_info.append({
                    'type': 'note_off',
                    'note': msg.note,
                    'time': current_time  # Time in seconds when the note is stopped
                })
    
    return notes_info

midi_file = r'C:\Users\isabe\OneDrive\Documents\TUFTS\ME35\pirates.mid'
midi_notes = parse_midi_file(midi_file)

# Now you have all the note data in the midi_notes variable
print(midi_notes)
