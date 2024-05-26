import numpy as np
import sounddevice as sd
import time
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

class MicrophoneFilter:
    def __init__(self):
        self.sampling_rate = 44100
        self.channels = 1
        self.recording = False
        self.original_audio = None
        self.filtered_audio = None
        self.start_time = None
        self.lowpass_cutoff = 1000  # Initial lowpass cutoff frequency
        self.highpass_cutoff = 200  # Initial highpass cutoff frequency

    def start_recording(self):
        self.recording = True
        self.original_audio = []
        self.filtered_audio = None
        self.start_time = time.time()
        self.update_timer_label()

        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.original_audio.append(indata.copy())

        def record_loop():
            with sd.InputStream(samplerate=self.sampling_rate, channels=self.channels, dtype='float32', callback=callback):
                print("Recording... Press Ctrl+C to stop.")
                while self.recording:
                    pass

        self.recording_thread = threading.Thread(target=record_loop)
        self.recording_thread.start()

    def stop_recording(self):
        self.recording = False
        self.recording_thread.join()  # Wait for the recording thread to finish
        self.original_audio = np.vstack(self.original_audio)  # Convert list of arrays to a single numpy array
        if self.original_audio is not None:
            self.filtered_audio = self.apply_filter(self.original_audio[:, 0])
        self.update_timer_label()
        plot_audio()  # Call plot_audio after stopping the recording

    def update_timer_label(self):
        if self.recording:
            duration = int(time.time() - self.start_time)
            timer_label.config(text=f"Recording duration: {duration} s")
            root.after(1000, self.update_timer_label)

    def play_original(self):
        if self.original_audio is not None:
            sd.play(self.original_audio, self.sampling_rate)

    def play_filtered(self):
        if self.filtered_audio is not None:
            sd.play(self.filtered_audio, self.sampling_rate)

    def apply_filter(self, input_signal):
        highpass_output = self.allpass_based_filter(input_signal, self.highpass_cutoff, self.sampling_rate, highpass=True,
                                                    amplitude=1.0)
        bandpass_output = self.allpass_based_filter(highpass_output, self.lowpass_cutoff, self.sampling_rate, highpass=False,
                                                    amplitude=1.0)
        return bandpass_output

    def a1_coefficient(self, break_frequency, sampling_rate):
        tan = np.tan(np.pi * break_frequency / sampling_rate)
        return (tan - 1) / (tan + 1)

    def allpass_filter(self, input_signal, break_frequency, sampling_rate):
        allpass_output = np.zeros_like(input_signal)
        dn_1 = 0
        a1 = self.a1_coefficient(break_frequency, sampling_rate)
        for n in range(input_signal.shape[0]):
            allpass_output[n] = a1 * input_signal[n] + dn_1
            dn_1 = input_signal[n] - a1 * allpass_output[n]
        return allpass_output

    def allpass_based_filter(self, input_signal, cutoff_frequency, sampling_rate, highpass=False, amplitude=1.0):
        allpass_output = self.allpass_filter(input_signal, cutoff_frequency, sampling_rate)
        if highpass:
            allpass_output *= -1
        filter_output = input_signal + allpass_output
        filter_output *= 0.5
        filter_output *= amplitude
        return filter_output


def start_recording():
    microphone_filter.start_recording()
    start_button.config(state="disabled")
    stop_button.config(state="normal")
    play_original_button.config(state="disabled")
    play_filtered_button.config(state="disabled")


def stop_recording():
    microphone_filter.stop_recording()
    start_button.config(state="normal")
    stop_button.config(state="disabled")
    play_original_button.config(state="normal")
    play_filtered_button.config(state="normal")


def play_original():
    microphone_filter.play_original()


def play_filtered():
    microphone_filter.play_filtered()


def plot_audio():
    if microphone_filter.original_audio is None or microphone_filter.filtered_audio is None:
        messagebox.showerror("Error", "No audio recorded yet.")
        return

    plt.clf()  # Clear the current figure

    duration_seconds = len(microphone_filter.original_audio) / microphone_filter.sampling_rate

    time_axis = np.linspace(0, duration_seconds, len(microphone_filter.original_audio))

    plt.plot(time_axis, microphone_filter.original_audio, label='Original Audio')
    plt.plot(time_axis, microphone_filter.filtered_audio, color='orange', label='Filtered Audio')

    # Customize x-axis labels
    plt.xlabel('Time (s)')
    plt.xticks(np.arange(0, duration_seconds + 1, step=max(1, duration_seconds // 10)))

    # Add y-axis label
    plt.ylabel('Amplitude')

    plt.title('Audio Signals')
    plt.legend()

    # Use canvas.get_tk_widget().pack_forget() to remove the previous plot
    for widget in graph_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(plt.gcf(), master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)


root = Tk()
root.title("Microphone Filter")

# Set default window size to accommodate the graph
root.geometry("1000x800")

microphone_filter = MicrophoneFilter()


start_button = Button(root, text="Start Record", command=start_recording)
start_button.pack(pady=5)

stop_button = Button(root, text="Stop Record", command=stop_recording, state="disabled")
stop_button.pack(pady=5)

play_original_button = Button(root, text="Play Original", command=play_original, state="disabled")
play_original_button.pack(pady=5)

play_filtered_button = Button(root, text="Play Filtered", command=play_filtered, state="disabled")
play_filtered_button.pack(pady=5)

timer_label = Label(root, text="Recording duration: 0 s")
timer_label.pack(pady=5)

# Create a frame to hold the graph
graph_frame = Frame(root)
graph_frame.pack(fill=BOTH, expand=1)

# Sliders for low-pass and high-pass filter cutoff frequencies
lowpass_slider_label = Label(root, text="Low-pass Cutoff Frequency")
lowpass_slider_label.pack(pady=(10, 0))

lowpass_slider = Scale(root, from_=0, to=2000, orient=HORIZONTAL, command=lambda value: update_lowpass_cutoff(value))
lowpass_slider.set(1000)  # Initial value
lowpass_slider.pack()

highpass_slider_label = Label(root,text="High-pass Cutoff Frequency")
highpass_slider_label.pack(pady=(10, 0))

highpass_slider = Scale(root, from_=0, to=2000, orient=HORIZONTAL, command=lambda value: update_highpass_cutoff(value))
highpass_slider.set(200)  # Initial value
highpass_slider.pack()


def update_lowpass_cutoff(value):
    microphone_filter.lowpass_cutoff = int(value)


def update_highpass_cutoff(value):
    microphone_filter.highpass_cutoff = int(value)


root.mainloop()

