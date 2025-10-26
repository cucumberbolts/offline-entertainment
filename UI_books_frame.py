import threading
import offline_books 
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button

class App:
    def __init__(self, root):
        self.root = root
        # Set window dimensions to match the Figma frame
        self.root.geometry("1440x900") 
        self.root.configure(bg="#FFFFFF") # Main background is white
        
        # --- Sidebar (Dark) ---
        self.sidebar_canvas = Canvas(
            self.root,
            bg="#212121", 
            height=900,
            width=260, 
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.sidebar_canvas.place(x=0, y=0)

        # --- "Scravel" Text (Updated) ---
        self.sidebar_canvas.create_text(
            30.0, 30.0, 
            anchor="nw",
            text="Scravel",
            fill="#FFFFFF", 
            font=("Inter", 24 * -1) 
        )

        # --- "Home" Button (Unselected) ---
        self.button_home = Button(
            self.sidebar_canvas, 
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Home button clicked"),
            relief="flat",
            text="Home",
            fg="#FFFFFF", 
            bg="#212121", 
            font=("Inter", 16 * -1),
            anchor="w",
            padx=30
        )
        self.button_home.place(
            x=0, y=100, 
            width=260, 
            height=50
        )
        
        # --- "Downloads" Text (Category Label) ---
        self.sidebar_canvas.create_text(
            30.0, 180.0, 
            anchor="nw",
            text="Downloads",
            fill="#A0A0A0", 
            font=("Inter", 16 * -1)
        )

        # --- "Videos" Button (Unselected) ---
        self.button_videos = Button(
            self.sidebar_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Videos button clicked"),
            relief="flat",
            text="▸ Videos",
            fg="#FFFFFF",
            bg="#212121",
            activebackground="#333333",
            activeforeground="#FFFFFF",
            font=("Inter", 16 * -1),
            anchor="w",
            padx=30
        )
        self.button_videos.place(x=0, y=230, width=260, height=50) 

        # --- "Music" Button (Unselected) ---
        self.button_music = Button(
            self.sidebar_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Music button clicked"),
            relief="flat",
            text="🎵 Music",
            fg="#FFFFFF",
            bg="#212121",
            activebackground="#333333",
            activeforeground="#FFFFFF",
            font=("Inter", 16 * -1),
            anchor="w",
            padx=30
        )
        self.button_music.place(x=0, y=280, width=260, height=50) 

        # --- "Books" Button (Selected) ---
        self.button_books = Button(
            self.sidebar_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=self.start_loading_books, # Command to reload books
            relief="flat",
            text="📚 Books",
            fg="#212121",     # Swapped to black text
            bg="#FFFFFF",     # Swapped to white background (selected)
            activebackground="#333333",
            activeforeground="#FFFFFF",
            font=("Inter", 16 * -1),
            anchor="w",
            padx=30
        )
        self.button_books.place(x=0, y=330, width=260, height=50) 

        # --- "Travel" Button (Unselected) ---
        self.button_travel = Button(
            self.sidebar_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Travel button clicked"),
            relief="flat",
            text="🗺️ Travel",
            fg="#FFFFFF",     # Swapped to white text
            bg="#212121",     # Swapped to dark background
            activebackground="#333333",
            activeforeground="#FFFFFF",
            font=("Inter", 16 * -1),
            anchor="w",
            padx=30
        )
        self.button_travel.place(x=0, y=380, width=260, height=50)
        
        
        # --- Main Content Area (White) ---
        self.main_canvas = Canvas(
            self.root,
            bg="#FFFFFF",
            height=900,
            width=1180, # 1440 - 260
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.main_canvas.place(x=260, y=0)


        # --- Tab Buttons ("Home", "New", "Seen") ---
        self.button_tab_home = Button(
            self.main_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Home tab clicked"),
            relief="flat",
            text="Home",
            fg="#212121",
            bg="#FFFFFF",
            font=("Inter", 16 * -1)
        )
        self.button_tab_home.place(x=50, y=30, width=80, height=40)

        self.main_canvas.create_rectangle(
            50.0, 70.0, 130.0, 73.0,
            fill="#0D63F7",
            outline=""
        )

        self.button_tab_new = Button(
            self.main_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("New tab clicked"),
            relief="flat",
            text="New",
            fg="#A0A0A0",
            bg="#FFFFFF",
            font=("Inter", 16 * -1)
        )
        self.button_tab_new.place(x=140, y=30, width=80, height=40)

        self.button_tab_seen = Button(
            self.main_canvas,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: print("Seen tab clicked"),
            relief="flat",
            text="Seen",
            fg="#A0A0A0",
            bg="#FFFFFF",
            font=("Inter", 16 * -1)
        )
        self.button_tab_seen.place(x=230, y=30, width=80, height=40)

        # --- Search Bar and Button REMOVED ---
        
        # --- "Clear Storage" Button ---
        self.button_clear = Button(
            self.main_canvas,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#A0A0A0", # Grey border
            command=self.clear_storage,
            relief="solid",
            text="Clear Storage",
            fg="#A0A0A0",
            bg="#FFFFFF",
            font=("Inter", 14)
        )
        # Repositioned button since search is gone
        self.button_clear.place(x=980, y=100, width=150, height=42) 

        # --- "Your Books" Text (Updated Header) ---
        self.main_canvas.create_text(
            50.0, 180.0,
            anchor="nw",
            text="Your Books", # Updated Header
            fill="#212121",
            font=("Inter", 18 * -1)
        )

        # --- Large Content Area (Placeholder) ---
        self.content_area = Text(
            self.main_canvas,
            bd=1,
            bg="#F5F5F5",
            fg="#000716",
            highlightthickness=1,
            highlightcolor="#E0E0E0",
            highlightbackground="#E0E0E0",
            relief="flat",
            font=("Inter", 14)
        )
        self.content_area.place(
            x=50.0, y=220.0,
            width=1080.0,
            height=650.0
        )
        self.content_area.insert("1.0", "Loading your books...")
        self.content_area.config(state="disabled")
        
        # --- Automatically load books on startup ---
        self.start_loading_books()


    def update_content_area(self, text):
        """Helper function to safely update the text area."""
        self.content_area.config(state="normal")
        self.content_area.delete("1.0", tk.END)
        self.content_area.insert("1.0", text)
        self.content_area.config(state="disabled")

    # --- NEW Book Loading Functions (replaces search functions) ---
    
    def start_loading_books(self):
        """
        Starts loading books in a new thread.
        This runs on the main UI thread.
        """
        self.update_content_area("Loading your downloaded books...")
        
        # Run the blocking file I/O task in a new thread
        load_thread = threading.Thread(
            target=self.run_book_loader_thread
        )
        load_thread.daemon = True # Allows app to close
        load_thread.start()

    def run_book_loader_thread(self):
        """
        Runs the actual book loading from files.
        This runs on a separate background thread.
        """
        try:
            # This is our new function from offline_books.py
            results = offline_books.get_all_downloaded_books_text()
        except Exception as e:
            results = f"An unexpected error occurred while loading books: {e}"
        
        # When done, schedule the UI update back on the main thread
        self.root.after(0, self.finish_loading_books, results)

    def finish_loading_books(self, results):
        """
        Updates the UI with results once the thread is done.
        This runs back on the main UI thread.
        """
        self.update_content_area(results)

    # --- END of new functions ---

    def clear_storage(self):
        """Clears the main content text area."""
        # Use your existing helper function to clear the text box
        self.update_content_area("Storage cleared. Click 'Books' to reload.")
        # Removed search bar reset logic
        self.root.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Scravel") # Updated window title
    app = App(root)
    root.resizable(False, False) # Resizing is unavailable
    root.mainloop()