import customtkinter as ctk
import yt_dlp
import subprocess
import os
import threading
import webbrowser
import sys

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DiscordSoundMaker(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Discord Sound Maker")
        self.geometry("500x400")

        # UI Elements
        self.label_url = ctk.CTkLabel(self, text="YouTube URL:")
        self.label_url.pack(pady=(20, 0))

        self.entry_url = ctk.CTkEntry(self, width=400)
        self.entry_url.pack(pady=(5, 10))

        # Frame for Start Time and Duration
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=10)

        # Start Time
        self.label_start_time = ctk.CTkLabel(self.controls_frame, text="Start Time (seconds):")
        self.label_start_time.grid(row=0, column=0, padx=(10, 0), pady=(0, 5))

        self.entry_start_time = ctk.CTkEntry(self.controls_frame, width=100)
        self.entry_start_time.insert(0, "0")
        self.entry_start_time.grid(row=1, column=0, padx=(10, 10), pady=(0, 10))

        # Duration
        self.label_duration = ctk.CTkLabel(self.controls_frame, text="Duration (seconds):")
        self.label_duration.grid(row=0, column=1, padx=(0, 10), pady=(0, 5))

        self.entry_duration = ctk.CTkEntry(self.controls_frame, width=100)
        self.entry_duration.insert(0, "5")
        self.entry_duration.grid(row=1, column=1, padx=(10, 10), pady=(0, 10))

        self.btn_download = ctk.CTkButton(self, text="Create Clip", command=self.start_download_thread)
        self.btn_download.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(pady=10)

    def update_status(self, text, color="white"):
        # Since this might be called from a thread, use after() to be thread-safe with tkinter
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def start_download_thread(self):
        url = self.entry_url.get().strip()
        start_time_str = self.entry_start_time.get().strip()
        duration_str = self.entry_duration.get().strip()

        if not url:
            self.update_status("Error: URL is empty", "red")
            return

        try:
            start_time = int(start_time_str)
        except ValueError:
            self.update_status("Error: Invalid start time", "red")
            return

        try:
            duration = int(duration_str)
            if duration <= 0:
                self.update_status("Error: Duration must be positive", "red")
                return
        except ValueError:
            self.update_status("Error: Invalid duration", "red")
            return

        # Cap duration at 15 seconds
        if duration > 15:
            duration = 15

        self.btn_download.configure(state="disabled")
        self.update_status("Downloading...", "yellow")

        thread = threading.Thread(target=self.download_clip, args=(url, start_time, duration))
        thread.daemon = True
        thread.start()

    def download_clip(self, url, start_time, duration):
        end_time = start_time + duration
        output_filename = "clip.mp3"
        
        # Remove existing clip if it exists to avoid conflicts
        if os.path.exists(output_filename):
            try:
                os.remove(output_filename)
            except Exception as e:
                self.update_status(f"Error: Could not remove old file: {e}", "red")
                self.after(0, lambda: self.btn_download.configure(state="normal"))
                return

        # yt-dlp command
        # Using --download-sections requires ffmpeg to be installed on the system
        command = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            f"--download-sections", f"*{start_time}-{end_time}",
            "-o", output_filename,
            url
        ]

        try:
            # Run the command via subprocess
            # capture_output=True allows us to capture errors if the command fails
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            if os.path.exists(output_filename):
                self.update_status("Success!", "green")
                # Open the folder containing the file
                folder = os.path.abspath(os.getcwd())
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder])
                else:
                    subprocess.run(["xdg-open", folder])
            else:
                self.update_status("Error: File not found after download", "red")

        except subprocess.CalledProcessError as e:
            # Extract error message from stderr
            error_msg = e.stderr if e.stderr else str(e)
            self.update_status(f"Error: {error_msg[:50]}...", "red")
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")
        finally:
            # Re-enable the button in the main thread
            self.after(0, lambda: self.btn_download.configure(state="normal"))

if __name__ == "__main__":
    app = DiscordSoundMaker()
    app.mainloop()
