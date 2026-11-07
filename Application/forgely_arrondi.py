"""Bouton arrondi Canvas compatible avec .pack et .configure(text=...)."""
import tkinter as tk

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, font, primary=False, palette=None):
        self._text=text
        self._command=command
        self._font=font
        self._primary=primary
        self._base='#778F35' if primary else '#494238'
        self._hover='#8FA64B' if primary else '#5A5144'
        self._text_color='#FFF7E9'
        if palette: self.set_palette(palette)
        self._parent_bg=parent.cget('bg')
        super().__init__(parent, bg=self._parent_bg, highlightthickness=0, bd=0,
                         height=39, cursor='hand2', takefocus=1)
        self._font_obj=None
        try:
            from tkinter import font as tkfont
            self._font_obj=tkfont.Font(root=self, font=font)
            width=self._font_obj.measure(text)+30
        except Exception:
            width=len(text)*8+30
        self.configure(width=max(82,width))
        self.bind('<Configure>',self._paint)
        self.bind('<Enter>',lambda e:self._paint(hover=True))
        self.bind('<Leave>',lambda e:self._paint())
        self.bind('<Button-1>',lambda e:self._command())
        self.bind('<Return>',lambda e:self._command())
        self.bind('<space>',lambda e:self._command())

    def set_palette(self,palette):
        self._base=palette['ACCENT'] if self._primary else palette['PANEL2']
        self._hover=palette['HOVER'] if self._primary else palette['BUTTON_HOVER']
        self._text_color=palette['BUTTON_FG'] if self._primary else palette['FG']
        if hasattr(self,'tk') and self.winfo_exists(): self._paint()

    def _paint(self,event=None,hover=False):
        self.delete('all')
        w=max(1,self.winfo_width());h=max(1,self.winfo_height());r=min(8,h//2,w//2)
        color=self._hover if hover else self._base
        # Smooth rounded rectangle: corners are genuine curves, not square buttons.
        self.create_polygon(r,1,w-r,1,w-1,r,w-1,h-r,w-r,h-1,r,h-1,1,h-r,1,r,
            smooth=True,splinesteps=24,fill=color,outline='')
        self.create_text(w/2,h/2,text=self._text,font=self._font,fill=self._text_color)

    def configure(self,cnf=None,**kw):
        if cnf: kw.update(cnf)
        if 'text' in kw:
            self._text=kw.pop('text')
            if getattr(self,'_font_obj',None):
                self.configure(width=max(82,self._font_obj.measure(self._text)+30))
        result=super().configure(**kw)
        if hasattr(self,'_text'): self._paint()
        return result
    config=configure

class RoundedCard(tk.Frame):
    """Panel with actual curved, anti-aliased corners (Pillow optional)."""
    def __init__(self, parent, bg='#302C26', radius=19):
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self._radius=radius
        self._card_color=bg
        self._outer_color=parent.cget('bg')
        self._corners=[]
        for anchor in ('nw','ne','sw','se'):
            corner=tk.Label(self, bg=self._outer_color, bd=0, highlightthickness=0)
            corner.place(relx=1 if 'e' in anchor else 0,
                         rely=1 if 's' in anchor else 0,anchor=anchor)
            self._corners.append((corner,anchor))
        self._corner_images=[]
        self.bind('<Configure>',self._redraw_corners)

    def _redraw_corners(self,event=None):
        try:
            from PIL import Image, ImageDraw, ImageTk
            r=self._radius
            images=[]
            for corner,anchor in self._corners:
                scale=3
                image=Image.new('RGB',(r*scale,r*scale),self._outer_color)
                draw=ImageDraw.Draw(image)
                # A quarter of a circular panel, with transparent-looking outer pixels.
                offsets={'nw':(0,0),'ne':(-r*scale,0),'sw':(0,-r*scale),'se':(-r*scale,-r*scale)}
                x,y=offsets[anchor]
                draw.ellipse((x,y,x+2*r*scale-1,y+2*r*scale-1),fill=self._card_color)
                photo=ImageTk.PhotoImage(image.resize((r,r),Image.Resampling.LANCZOS),master=self)
                corner.configure(image=photo,width=r,height=r)
                corner.lift()
                images.append(photo)
            self._corner_images=images
        except (ImportError,tk.TclError):
            pass
