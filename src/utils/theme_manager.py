class ThemeManager:
    def __init__(self):
        self.dark_theme = {
            "bg": "#0A1929", 
            "surface": "#132F4C", 
            "accent": "#007FFF", 
            "accent_secondary": "#00C6FF", 
            "text": "#FFFFFF",
            "text_secondary": "#B2BAC2",
            "border": "#1E4976",  
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#FF5252",
            "gradient": ["#007FFF", "#00C6FF"]  
        }
        
        self.light_theme = {
            "bg": "#F3F6F9", 
            "surface": "#FFFFFF",
            "accent": "#0059B2",  
            "accent_secondary": "#007FFF",
            "text": "#1A2027",
            "text_secondary": "#3E5060",
            "border": "#E7EBF0",
            "success": "#2E7D32",
            "warning": "#ED6C02",
            "error": "#D32F2F",
            "gradient": ["#0059B2", "#007FFF"]
        }
        
        self.current_theme = self.dark_theme
        self.is_dark = True

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.current_theme = self.dark_theme if self.is_dark else self.light_theme
        return self.current_theme 