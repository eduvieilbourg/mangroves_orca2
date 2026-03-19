#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Graphical column selector for CSV input.

Provides a Tkinter-based interface to:
- select longitude, latitude, and value columns
- define a masking rule for non-numeric values

Author
------
Eric Duvieilbourg (CNRS / LEMAR)

License
-------
MIT
"""
# from orca2_tk_column_selector.py by eduvieilbourg

import tkinter as tk
from tkinter import messagebox, ttk
import polars as pl 

class ColumnSelector(tk.Toplevel):
    """
    Fenêtre modale utilisant des Radiobuttons pour la sélection unique 
    des colonnes Lon, Lat, Val et la définition de la valeur de masque.
    """
    def __init__(self, master, available_cols, val_col_dtype):
        super().__init__(master)
        self.title("Sélection des Colonnes & Masque")
        self.transient(master)  
        self.grab_set()         
        
        self.available_cols = available_cols
        
        # Variables de contrôle pour les Radiobuttons (Stocke le nom de la colonne sélectionnée)
        self.lon_col_var = tk.StringVar(self, value="Intersect_lon" if "Intersect_lon" in available_cols else available_cols[0])
        self.lat_col_var = tk.StringVar(self, value="Intersect_lat" if "Intersect_lat" in available_cols else available_cols[0])
        self.val_col_var = tk.StringVar(self, value="flag_sandy" if "flag_sandy" in available_cols else available_cols[0])
        
        # Le masque par défaut est "1" pour couvrir Booléen/Entier/Texte
        self.mask_val = tk.StringVar(self, value="1") 
        self.result = None
        self.val_col_dtype = val_col_dtype
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Sélections des colonnes ---
        selection_frame = ttk.LabelFrame(main_frame, text="Sélection des Colonnes")
        selection_frame.pack(fill="x", padx=5, pady=5)
        
        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(1, weight=1)
        selection_frame.grid_columnconfigure(2, weight=1)
        
        # Titres des groupes
        ttk.Label(selection_frame, text="Longitude (Lon)", font='TkDefaultFont 10 bold').grid(row=0, column=0, padx=5, pady=5, sticky="n")
        ttk.Label(selection_frame, text="Latitude (Lat)", font='TkDefaultFont 10 bold').grid(row=0, column=1, padx=5, pady=5, sticky="n")
        ttk.Label(selection_frame, text="Valeur (Val)", font='TkDefaultFont 10 bold').grid(row=0, column=2, padx=5, pady=5, sticky="n")
        
        # Création des Radiobuttons
        row_idx = 1
        for col_name in self.available_cols:
            rb_lon = ttk.Radiobutton(selection_frame, text=col_name, variable=self.lon_col_var, value=col_name)
            rb_lon.grid(row=row_idx, column=0, padx=5, sticky="w")
            
            rb_lat = ttk.Radiobutton(selection_frame, text=col_name, variable=self.lat_col_var, value=col_name)
            rb_lat.grid(row=row_idx, column=1, padx=5, sticky="w")
            
            rb_val = ttk.Radiobutton(selection_frame, text=col_name, variable=self.val_col_var, value=col_name, 
                                     command=self.show_dtype_info)
            rb_val.grid(row=row_idx, column=2, padx=5, sticky="w")
            
            row_idx += 1
            
        # --- Affichage du type de donnée et Masque ---

        dtype_str = self.val_col_dtype.get(self.val_col_var.get())
        self.dtype_label = ttk.Label(main_frame, text=f"Type de la colonne Valeur: {dtype_str}")
        self.dtype_label.pack(fill="x", padx=5, pady=(10, 5))
        
        # Frame pour la valeur de masque
        # NOUVEAU LIBELLÉ
        self.mask_frame = ttk.LabelFrame(main_frame, text="Définition de la Valeur 'Valide' (Conversion en 1.0)")
        self.mask_frame.pack(padx=5, pady=5, fill="x")
        self.mask_frame.pack_forget()

        # NOUVEAU TEXTE D'INSTRUCTION
        ttk.Label(self.mask_frame, text="Saisissez la valeur exacte à convertir en **1.0** (ex: 'True', '1', 'Sable'):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ttk.Entry(self.mask_frame, textvariable=self.mask_val).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.mask_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.mask_frame, text="Toutes les autres valeurs (y compris les vides et les majuscules/minuscules différentes) seront converties en 0.0.").grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Bouton OK
        ttk.Button(self, text="Valider les Sélections", command=self.on_ok).pack(pady=10)
        
        # Appel initial pour afficher/cacher le masque correctement
        self.show_dtype_info()


    def show_dtype_info(self):
        col_name = self.val_col_var.get()
        dtype = self.val_col_dtype.get(col_name)
        
        self.dtype_label.config(text=f"Type de la colonne Valeur: {dtype}")
        
        # 📌 CORRECTION : Afficher le masque pour TOUS les types qui ne sont pas Float/Double.
        # Car l'utilisateur peut vouloir mapper True/False, 1/0 ou des chaînes.
        is_float_type = dtype.startswith("Float") or dtype.startswith("F64") or dtype.startswith("F32")
        
        if not is_float_type:
            self.mask_frame.pack(padx=5, pady=5, fill="x")
        else:
            self.mask_frame.pack_forget()

        self.update_idletasks()

    def on_ok(self):
        try:
            lon = self.lon_col_var.get()
            lat = self.lat_col_var.get()
            val = self.val_col_var.get()
            
            if lon == lat or lon == val or lat == val:
                messagebox.showerror("Erreur de sélection", "Les colonnes Lon, Lat et Val doivent être uniques.")
                return

            dtype_str = self.val_col_dtype.get(val)
            mask_val_str = None

            is_float_type = dtype_str.startswith("Float") or dtype_str.startswith("F64") or dtype_str.startswith("F32")

            if not is_float_type:
                # Si le masque est visible (type non-float), on récupère la chaîne de masque
                mask_val_str = self.mask_val.get()
                if not mask_val_str.strip():
                     messagebox.showerror("Erreur de saisie", "Veuillez spécifier une valeur de masque (ex: 1, True ou 'sable').")
                     return
            
            # On retourne la chaîne si le masque est utilisé, sinon None.
            self.result = (lon, lat, val, mask_val_str) 
            self.destroy() 
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite lors de la validation : {e}")

    def show(self):
        self.deiconify()
        self.update() 
        self.master.wait_window(self)
        return self.result
