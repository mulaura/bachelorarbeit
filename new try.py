from tkinter import *
import tkinter.messagebox
from tkinter import ttk
import requests
from threading import Thread
from nexstar import NexStar
import astropy
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS
from astropy.coordinates import Galactic
from datetime import datetime
import pandas as pd
import io
import csv
import webbrowser
import subprocess





class Window(Frame):

        def __init__(self, master=None):

            Frame.__init__(self, master)
            self.master = master

            self.port = "COM5"
            self.active = False
            self.aligned = False
            self.location = [47.3686498, 8.5391825]

            #################
            # CONNECT FRAME
            #################
            self.connect_frame = LabelFrame(self.master, text="Connect to the Mount", bd=5)
            self.connect_frame.place(rely = 0.025, anchor = 'n', relx = 0.25, relwidth=0.4, relheight=0.2)

            #Button+Connection Status
            self.active = False
            self.var_connection_status = StringVar()
            self.var_connection_status.set('Not Connected')
            self.active_var = StringVar()
            self.active_var.set('OFF')
            self.activation_button = Button(self.connect_frame, textvariable=self.active_var,  command=self.init_mount, bg='firebrick2') #command fehlt hier
            self.activation_button.place(relx=0.1, rely=0.1, relwidth=0.2, relheight=0.4, anchor='nw')
            self.connection_status = Label(self.connect_frame, textvariable=self.var_connection_status)
            self.connection_status.place(relx=0.5, rely=0.1, anchor='nw')
            self.active = False

            #Information about Initialisation
            self.var_port = StringVar()
            self.var_port.set("USB-Port: " + self.port)
            self.port_label = Label(self.connect_frame, textvariable=self.var_port)
            self.port_label.place(relx = 0.5, rely = 0.3, anchor='nw')

            #ChangePort
            self.entry_label_text = StringVar()
            self.entry_label_text.set("USB-Port:")
            self.port_entry_label = Label(self.connect_frame, textvariable=self.entry_label_text)
            self.port_entry_label.place(relx=0.05, rely = 0.7, relwidth=0.25, relheight=0.1, anchor='nw')
            self.port_entry = Entry(self.connect_frame)
            self.port_entry.place(relx=0.35, rely=0.65, relwidth=0.3, relheight=0.2)
            self.button_change_port = Button(self.connect_frame, text="Change", command=lambda: self.change_port(self.port_entry.get()))
            self.button_change_port.place(relx=0.7, rely=0.65, relwidth=0.25, relheight = 0.2)


            ################
            # Info frame
            #################
            self.info_frame = LabelFrame(self.master, text="Position", bd=5)
            self.info_frame.place(rely=0.275, relx = 0.25, relwidth = 0.4, relheight = 0.15, anchor='n')

            self.current_radec_var = StringVar()
            self.current_radec_var.set("RA: 0.0, DEC: 90.0")
            #self.update_RADEC()
            self.current_radec_label = Label(self.info_frame, textvariable=self.current_radec_var)
            self.current_radec_label.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.3, anchor='nw')
            self.RADEC_thread = Thread(target=self.update_RADEC())
            self.RADEC_thread.start()


            self.sidereal_var = StringVar()
            self.update_LST()
            self.sidereal_label = Label(self.info_frame, textvariable=self.sidereal_var)
            self.sidereal_label.place(relx=0.1, rely=0.5, relwidth=0.8, relheight=0.3, anchor='nw')
            self.lst_thread = Thread(target=self.update_LST)
            self.lst_thread.start()


            #####################
            # GoTo Frame
            #####################

            self.GoTo_frame = LabelFrame(self.master, text="GoTo Options", bd=5)
            self.GoTo_frame.place(rely=0.475, relx=0.25, relwidth=0.4, relheight=0.5, anchor='n')

            #goto with ra/dec input

            self.GoTo_RaDec_LabelFrame = LabelFrame(self.GoTo_frame, text="GoTo with Radial/Declination Coordinates")
            self.GoTo_RaDec_LabelFrame.place(rely=0.025, relx=0.5, relwidth=0.95, relheight=0.4, anchor='n')
            self.RA = StringVar()
            self.RA.set("90.0")
            self.DEC = StringVar()
            self.DEC.set("0.0")

            self.Ask_Ra_var= StringVar()
            self.Ask_Ra_var.set("Right Ascension: ")
            self.GoTo_ask_Ra_Label = Label(self.GoTo_RaDec_LabelFrame, textvariable=self.Ask_Ra_var, anchor='e')
            self.GoTo_ask_Ra_Label.place(relx=0.025, rely=0.15, relwidth=0.3, relheight=0.2, anchor='nw')
            self.Ask_Ra_entry = Entry(self.GoTo_RaDec_LabelFrame, textvariable=self.RA, width=10)
            self.Ask_Ra_entry.place(relx=0.35, rely=0.15, relwidth=0.4, relheight=0.2, anchor='nw')

            self.Ask_Dec_var = StringVar()
            self.Ask_Dec_var.set("Declination: ")
            self.GoTo_ask_Dec_Label = Label(self.GoTo_RaDec_LabelFrame, textvariable=self.Ask_Dec_var, anchor='e')
            self.GoTo_ask_Dec_Label.place(relx=0.025, rely=0.45, relwidth=0.3, relheight=0.2, anchor='nw')
            self.Ask_Dec_entry = Entry(self.GoTo_RaDec_LabelFrame,textvariable=self.DEC, width=10)
            self.Ask_Dec_entry.place(relx=0.35, rely=0.45, relwidth=0.4, relheight=0.2, anchor='nw')

            self.GoTo_RaDec_Status = StringVar()
            self.GoTo_RaDec_Status.set(" --- ")
            self.GoTo_RaDec_Status_Label = Label(self.GoTo_RaDec_LabelFrame, textvariable = self.GoTo_RaDec_Status)
            self.GoTo_RaDec_Status_Label.place(relx=0.5, rely=0.8, relwidth=0.95, relheight=0.2, anchor='center')

            self.GoTo_RaDec_Button = Button(self.GoTo_RaDec_LabelFrame, text="GoTo", command=lambda: self.GoTo__RaDec(self.Ask_Ra_entry.get(), self.Ask_Dec_entry.get()))
            self.GoTo_RaDec_Button.place(relx=0.8, rely=0.45, relwidth=0.175, relheight=0.2, anchor='nw')
            self.Abort_RaDec_Button = Button(self.GoTo_RaDec_LabelFrame, text="Abort", command=lambda: self.Abort_GoTo_RaDec())
            self.Abort_RaDec_Button.place(relx=0.8, rely=0.15, relwidth=0.175, relheight=0.2, anchor='nw')


            # goto with arrows

            self.GoTo_Arrow_LabelFrame= LabelFrame(self.GoTo_frame, text="Move Mount with Arrows")
            self.GoTo_Arrow_LabelFrame.place(rely=0.45, relx=0.5, relwidth=0.95, relheight=0.525, anchor='n')

            self.arrow_frame = Frame(self.GoTo_Arrow_LabelFrame, bg="grey")
            self.arrow_frame.place(rely=0.5, relx=0.5, relwidth=0.5, relheight=0.8, anchor='center')

            self.slewing = False
            self.slewing_ax = None
            self.slewrate_var = StringVar()
            self.slewrate_var.set('1000')
            self.slewrate_entry = Entry(self.arrow_frame, textvariable=self.slewrate_var, width=10)
            self.slewrate_entry.bind("<Return>", self.set_slewrate)
            self.ra_up_btn = Button(self.arrow_frame, text='RA +', command=lambda: self.slew('ra', 1))
            self.ra_down_btn = Button(self.arrow_frame, text='RA -', command=lambda: self.slew('ra', -1))
            self.dec_up_btn = Button(self.arrow_frame, text='DEC +', command=lambda: self.slew('dec', 1))
            self.dec_down_btn = Button(self.arrow_frame, text='DEC -', command=lambda: self.slew('dec', -1))

            self.ra_up_btn.place(anchor='center', relx=0.85, rely=0.5, relwidth=0.25, relheight=0.2)
            self.ra_down_btn.place(anchor='center', relx=0.15, rely=0.5, relwidth=0.25, relheight=0.2)
            self.dec_up_btn.place(anchor='center', relx=0.5, rely=0.2, relwidth=0.25, relheight=0.2)
            self.dec_down_btn.place(anchor='center', relx=0.5, rely=0.8, relwidth=0.25, relheight=0.2)
            self.slewrate_entry.place(anchor='center', relx=0.5, rely=0.5, relwidth=0.35, relheight=0.2)

            ##############################
            # Tab Frame
            ##############################
            self.Tab_frame = LabelFrame(self.master, bd=5)
            self.Tab_frame.place(rely=0.025, relx=0.75, relwidth=0.4, relheight=0.95, anchor='n')

            self.tabControl = ttk.Notebook(self.Tab_frame)
            self.tabControl.place()
            self.Alignment_frame = ttk.Frame(self.tabControl)
            self.Measurment_frame = ttk.Frame(self.tabControl)

            self.tabControl.add(self.Alignment_frame, text='Alignment')
            self.tabControl.add(self.Measurment_frame, text='Measurement')
            self.tabControl.pack(expand=1, fill="both")


            ##############################
            # Alignment Frame
            ##############################

            #Chose Coordinates Frame

            self.Choose_Coordinate_Frame = LabelFrame(self.Alignment_frame, text="1. Choose Coordinates", bd=5)
            self.Choose_Coordinate_Frame.place(relx=0.5, rely=0.025, relwidth=0.95, relheight=0.35, anchor="n")

            #DropDownMenu
            self.ObjectList = ["Object", "Zenith", "Moon", "Sun", "Polaris"]

            self.ObjectLabelVar = StringVar()
            self.ObjectLabelVar.set("Choose one Object for Alignment:")
            self.ObjectLabel = Label(self.Choose_Coordinate_Frame, textvariable = self.ObjectLabelVar, anchor='w')
            self.ObjectLabel.place(relx=0.05, rely=0.05, relheight=0.15, relwidth=0.6, anchor='nw')
            self.ObjectVar = StringVar()
            self.ObjectVar.set(self.ObjectList[0])

            self.ObjectMenu = OptionMenu(self.Choose_Coordinate_Frame, self.ObjectVar, *self.ObjectList)
            self.ObjectMenu.place(relx=0.05, rely=0.2, relheight=0.15, relwidth=0.5, anchor='nw')

            self.SelectObjectButton = Button(self.Choose_Coordinate_Frame, text="Select", command=lambda: self.choose_object( self.ObjectVar.get()))
            self.SelectObjectButton.place(relx=0.65, rely=0.2, relheight=0.15, relwidth=0.25, anchor='nw')

            #Entry Fild/ Showing Chosen RA/DEC Coordinates

            self.Alignment_EntryLabelVar = StringVar()
            self.Alignment_EntryLabelVar.set("Or give the RA and DEC of the object:")
            self.Alignment_EntryLabel = Label(self.Choose_Coordinate_Frame, textvariable=self.Alignment_EntryLabelVar, anchor="nw")
            self.Alignment_EntryLabel.place(relx=0.05, rely=0.45, relwidth = 0.65, relheight= 0.15, anchor='nw')

            self.Alignment_RA_EntryLabelVar = StringVar()
            self.Alignment_DEC_EntryLabelVar = StringVar()
            self.Alignment_RA_EntryLabelVar.set("RA:")
            self.Alignment_DEC_EntryLabelVar.set("DEC:")
            self.Alignment_RA_EntryLabel = Label(self.Choose_Coordinate_Frame, textvariable=self.Alignment_RA_EntryLabelVar)
            self.Alignment_DEC_EntryLabel = Label(self.Choose_Coordinate_Frame, textvariable=self.Alignment_DEC_EntryLabelVar)
            self.Alignment_RA_EntryLabel.place(relx=0.05, rely=0.65, relwidth = 0.2, relheight= 0.15, anchor='nw')
            self.Alignment_DEC_EntryLabel.place(relx=0.05, rely=0.8, relwidth=0.2, relheight=0.15, anchor='nw')

            self.Alignment_RA = StringVar()
            self.Alignment_RA.set("90.0")
            self.Alignment_DEC = StringVar()
            self.Alignment_DEC.set("0.0")
            self.Alignment_RA_Entry = Entry(self.Choose_Coordinate_Frame, textvariable=self.Alignment_RA, width=10)
            self.Alignment_RA_Entry.place(relx=0.3, rely=0.65, relwidth = 0.3, relheight= 0.125, anchor='nw')
            self.Alignment_DEC_Entry = Entry(self.Choose_Coordinate_Frame, textvariable=self.Alignment_DEC, width=10)
            self.Alignment_DEC_Entry.place(relx=0.3, rely=0.8, relwidth = 0.3, relheight= 0.125, anchor='nw')

            #GoTo Target Frame
            self.Alignment_GoTo_Frame = LabelFrame(self.Alignment_frame, text="2. Let Telescope move to chosen object", bd=5)
            self.Alignment_GoTo_Frame.place(relx=0.5, rely=0.375, relwidth=0.95, relheight=0.15, anchor="n")

            self.Alignment_GoTo_Button = Button(self.Alignment_GoTo_Frame, text="GoTo", command=lambda: self.GoTo_Alignment(self.Alignment_RA_Entry.get(), self.Alignment_DEC_Entry.get()))
            self.Alignment_GoTo_Button.place(relx=0.1, rely=0.1, relwidth=0.35, relheight=0.3, anchor='nw')
            self.Alignment_Abort_Button = Button(self.Alignment_GoTo_Frame, text="Abort", command=lambda: self.Abort_GoTo_Alignment())
            self.Alignment_Abort_Button.place(relx=0.55, rely=0.1, relwidth=0.35, relheight=0.3, anchor='nw')

            self.Alignment_GoTo_LabelVar = StringVar()
            self.Alignment_GoTo_LabelVar.set(" --- ")
            self.Alignment_GoTo_Label = Label(self.Alignment_GoTo_Frame, textvariable=self.Alignment_GoTo_LabelVar)
            self.Alignment_GoTo_Label.place(relx=0.5, rely=0.8, relwidth=0.9, relheight=0.35, anchor = "center")

            #Allign Telescope with Object

            self.Alignment_Slew_Frame = LabelFrame(self.Alignment_frame, text="3. Slew Telesope to point the chosen object", bd=5)
            self.Alignment_Slew_Frame.place(relx=0.5, rely=0.525, relheight=0.275, relwidth=0.95, anchor= "n")

            self.Alignment_arrow_frame = Frame(self.Alignment_Slew_Frame, bg="grey")
            self.Alignment_arrow_frame.place(rely=0.5, relx=0.5, relwidth=0.55, relheight=0.8, anchor='center')

            self.Alignment_slewing = False
            self.slewing_ax = None
            self.Alignment_slewrate_var = StringVar()
            self.Alignment_slewrate_var.set('1000')
            self.Alignment_slewrate_entry = Entry(self.Alignment_arrow_frame, textvariable=self.Alignment_slewrate_var, width=10)
            self.Alignment_slewrate_entry.bind("<Return>", self.Alignment_set_slewrate)
            self.Alignment_ra_up_btn = Button(self.Alignment_arrow_frame, text='RA +', command=lambda: self.Alignment_slew('ra', 1))
            self.Alignment_ra_down_btn = Button(self.Alignment_arrow_frame, text='RA -', command=lambda: self.Alignment_slew('ra', -1))
            self.Alignment_dec_up_btn = Button(self.Alignment_arrow_frame, text='DEC +', command=lambda: self.Alignment_slew('dec', 1))
            self.Alignment_dec_down_btn = Button(self.Alignment_arrow_frame, text='DEC -', command=lambda: self.Alignment_slew('dec', -1))

            self.Alignment_ra_up_btn.place(anchor='center', relx=0.85, rely=0.5, relwidth=0.25, relheight=0.2)
            self.Alignment_ra_down_btn.place(anchor='center', relx=0.15, rely=0.5, relwidth=0.25, relheight=0.2)
            self.Alignment_dec_up_btn.place(anchor='center', relx=0.5, rely=0.2, relwidth=0.25, relheight=0.2)
            self.Alignment_dec_down_btn.place(anchor='center', relx=0.5, rely=0.8, relwidth=0.25, relheight=0.2)
            self.Alignment_slewrate_entry.place(anchor='center', relx=0.5, rely=0.5, relwidth=0.35, relheight=0.2)



            #Synchronise Telescope Position with coordinates

            self.Alignment_Sync_Frame= LabelFrame(self.Alignment_frame, text="4. Synchronise Telescope position with chosen coordinates", bd=5)
            self.Alignment_Sync_Frame.place(relx=0.5, rely=0.8, relheight=0.175, relwidth=0.95, anchor= "n")

            self.Alignment_Sync_Frame_LabelVar = StringVar()
            self.Alignment_Sync_Frame_LabelVar.set("When Telescope is aligned, synchronise the telescope\nby pressing:")
            self.Alignment_Sync_Frame_Label = Label(self.Alignment_Sync_Frame, textvar=self.Alignment_Sync_Frame_LabelVar, anchor="center")
            self.Alignment_Sync_Frame_Label.place(relx=0.05, rely=0.05, relwidth=0.95, relheight=0.5, anchor="nw")

            self.Sync_Button = Button(self.Alignment_Sync_Frame, text="Synchronise", command=lambda: self.Synchronize(self.Alignment_RA_Entry.get(), self.Alignment_DEC_Entry.get()))
            self.Sync_Button.place(relx=0.5, rely=0.7, relwidth=0.4, relheight=0.3, anchor="center")

            ##############################
            # Measurment Frame
            ##############################


            ##############################
            #Measurment Frame 1
            ##############################

            self.Measurment_Frame_1 = LabelFrame(self.Measurment_frame, text="One Measurment", bd=5)
            self.Measurment_Frame_1.place(relx=0.5, rely=0.025, relwidth=0.95, relheight=0.2, anchor="n")

            self.Measurment_Frame_1_LabelVar = StringVar()
            self.Measurment_Frame_1_LabelVar.set("1. Use right side to move to the coordinates in the sky. \n "
                                                 "When the telescope is pointed to the correct direction \n"
                                                 "start the measurment.")
            self.Measurment_Frame_1_Label = Label(self.Measurment_Frame_1, textvar=self.Measurment_Frame_1_LabelVar, anchor= "center")
            self.Measurment_Frame_1_Label.place(relx=0.5, rely=0.05, relwidth=0.95, relheight=0.6, anchor="n")

            self.Measurment_Frame_1_Button = Button(self.Measurment_Frame_1, text="Measure", command=lambda: self.Measure())
            self.Measurment_Frame_1_Button.place(relx=0.5, rely=0.65, relwidth=0.4, relheight=0.25, anchor="n")


            ##########################
            #Measurment Frame 2
            ##########################

            #Calculating Coordinates from Galactic Cooridinates and Number of Measurments

            self.Measurment_Frame_2 = LabelFrame(self.Measurment_frame, text="Milky Way Measurment", bd=5)
            self.Measurment_Frame_2.place(relx=0.5, rely=0.25, relwidth=0.95, relheight=0.725, anchor="n")

            self.Measurment_Frame_2_LabelVar1 = StringVar()
            self.Measurment_Frame_2_LabelVar1.set("Please enter the coordinates of the Milky Way section \n" +
                                                 "you want to scan: ")
            self.Measurment_Frame_2_Label1 = Label(self.Measurment_Frame_2, textvar=self.Measurment_Frame_2_LabelVar1, anchor="nw")
            self.Measurment_Frame_2_Label1.place(relx=0.5, rely=0.05, relwidth=0.95, relheight=0.1, anchor="n")

            self.GalLong1 = StringVar()
            self.GalLong1.set("90.0")
            self.GalLong2 = StringVar()
            self.GalLong2.set("90.0")
            self.GalLat1 = StringVar()
            self.GalLat1.set("0.0")
            self.GalLat2 = StringVar()
            self.GalLat2.set("0.0")
            self.GalLong1_Entry= Entry(self.Measurment_Frame_2, textvariable=self.GalLong1, width=10)
            self.GalLong1_Entry.place(relx=0.2, rely=0.15, relwidth=0.2, relheight=0.05, anchor='nw')
            self.GalLong2_Entry = Entry(self.Measurment_Frame_2, textvariable=self.GalLong2, width=10)
            self.GalLong2_Entry.place(relx=0.7, rely=0.15, relwidth=0.2, relheight=0.05, anchor='nw')
            self.GalLat1_Entry = Entry(self.Measurment_Frame_2, textvariable=self.GalLat1, width=10)
            self.GalLat1_Entry.place(relx=0.2, rely=0.225, relwidth=0.2, relheight=0.05, anchor='nw')
            self.GalLat2_Entry = Entry(self.Measurment_Frame_2, textvariable=self.GalLat2, width=10)
            self.GalLat2_Entry.place(relx=0.7, rely=0.225, relwidth=0.2, relheight=0.05, anchor='nw')

            self.Ask_GalLong1_var = StringVar()
            self.Ask_GalLong1_var.set("Start l: ")
            self.Ask_GalLong1_Label = Label(self.Measurment_Frame_2, textvariable=self.Ask_GalLong1_var, anchor='e')
            self.Ask_GalLong1_Label.place(relx=0.025, rely=0.15, relwidth=0.15, relheight=0.05, anchor='nw')
            self.Ask_GalLong2_var = StringVar()
            self.Ask_GalLong2_var.set("End l: ")
            self.Ask_GalLong2_Label = Label(self.Measurment_Frame_2, textvariable=self.Ask_GalLong2_var, anchor='e')
            self.Ask_GalLong2_Label.place(relx=0.525, rely=0.15, relwidth=0.15, relheight=0.05, anchor='nw')
            self.Ask_GalLat1_var = StringVar()
            self.Ask_GalLat1_var.set("Start b: ")
            self.Ask_GalLat1_Label = Label(self.Measurment_Frame_2, textvariable=self.Ask_GalLat1_var, anchor='e')
            self.Ask_GalLat1_Label.place(relx=0.025, rely=0.225, relwidth=0.15, relheight=0.05, anchor='nw')
            self.Ask_GalLat2_var = StringVar()
            self.Ask_GalLat2_var.set("End b: ")
            self.Ask_GalLat2_Label = Label(self.Measurment_Frame_2, textvariable=self.Ask_GalLat2_var, anchor='e')
            self.Ask_GalLat2_Label.place(relx=0.525, rely=0.225, relwidth=0.15, relheight=0.05, anchor='nw')


            self.Measurment_Frame_2_LabelVar2 = StringVar()
            self.Measurment_Frame_2_LabelVar2.set("Please enter here the number of measurements \n"
                                                  "you want to do in this galactic section (min. 2):")
            self.Measurment_Frame_2_Label2 = Label(self.Measurment_Frame_2, textvar=self.Measurment_Frame_2_LabelVar2,
                                                   anchor="nw")
            self.Measurment_Frame_2_Label2.place(relx=0.5, rely=0.35, relwidth=0.95, relheight=0.1, anchor="n")

            self.NumMeasurments = StringVar()
            self.NumMeasurments.set("10")
            self.NumMeasurments_Entry = Entry(self.Measurment_Frame_2, textvariable=self.NumMeasurments, width=10)
            self.NumMeasurments_Entry.place(relx=0.6, rely=0.45, relwidth=0.2, relheight=0.05, anchor='nw')
            self.Ask_NumMeasurments_var = StringVar()
            self.Ask_NumMeasurments_var.set("Number of Measurments: ")
            self.Ask_NumMeasurments_Label = Label(self.Measurment_Frame_2, textvariable=self.Ask_NumMeasurments_var, anchor='e')
            self.Ask_NumMeasurments_Label.place(relx=0.025, rely=0.45, relwidth=0.5, relheight=0.05, anchor='nw')

            self.Calculate_csv_filename = StringVar()
            self.Calculate_csv_filename.set("coordinates.csv")
            self.Calculate_csv_filename_Entry = Entry(self.Measurment_Frame_2, textvariable=self.Calculate_csv_filename, width=10)
            self.Calculate_csv_filename_Entry.place(relx=0.25, rely=0.55, relheight=0.05, relwidth=0.4, anchor="n")
            self.Calculate_Button = Button(self.Measurment_Frame_2, text="Calculate Coordinates", command=lambda:self.calculate_coordinates_measurement(self.Calculate_csv_filename_Entry.get()))
            self.Calculate_Button.place(relx=0.75, rely=0.55, relheight=0.05, relwidth=0.4, anchor="n")

            self.Open_csv_filename = StringVar()
            self.Open_csv_filename.set("coordinates.csv")
            self.Open_csv_filename_Entry = Entry(self.Measurment_Frame_2, textvariable=self.Open_csv_filename, width=10)
            self.Open_csv_filename_Entry.place(relx=0.25, rely=0.65, relheight=0.05, relwidth=0.4, anchor="n")
            self.Open_csv_filename_Entry.bind("<Return>", self.MessageInMessageFrame_update)
            self.Open_CSV_Button = Button(self.Measurment_Frame_2, text="Open CSV", command=lambda:self.open_csv(self.Open_csv_filename_Entry.get()))
            self.Open_CSV_Button.place(relx=0.75, rely=0.65, relheight=0.05, relwidth=0.4, anchor="n")

            self.Measurment_Frame_2_LabelVar3 = StringVar()
            self.MessageInMessageFrame = "If you want to start the measurment from the file\n'" + self.Open_csv_filename_Entry.get() + "'\npress the 'Start Measurment'-Button."
            self.Measurment_Frame_2_LabelVar3.set(self.MessageInMessageFrame)
            self.Measurment_Frame_2_Label3 = Label(self.Measurment_Frame_2, textvar=self.Measurment_Frame_2_LabelVar3,
                                                   anchor="nw")
            self.Measurment_Frame_2_Label3.place(relx=0.5, rely=0.75, relwidth=0.95, relheight=0.15, anchor="n")

            self.Measurment_Frame_2_Button = Button(self.Measurment_Frame_2, text="Start Measurment", command=lambda: self.MilkyWayGalaxy_Measurment(self.Open_csv_filename_Entry.get()))
            self.Measurment_Frame_2_Button.place(relx=0.5, rely=0.9, relwidth=0.6, relheight=0.05, anchor="n")

        def choose_object(self, TargetObject): 
            '''
            
            :param TargetObject: This function calls the chosen object (Moon, Sun, Polaris) and inserts their coordinates in the Ra/Dec Fields.
                        (Note: Coordinates for Zenith are missing)
            :return: 
            Return Error if Insertion did not work.
            Return Error if No Object was choosen
            '''
            Target = TargetObject
            print('\n%s was chosen for Alignment  \n\n' % (Target))
            self.Alignment_RA_Entry.delete(0, END)
            self.Alignment_DEC_Entry.delete(0, END)
            try:
                t = Time(datetime.utcnow(), scale="utc")
                if Target == "Object":
                    self.Error("No Object chosen.")
                if Target == "Sun":
                    coordinates = astropy.coordinates.get_sun(time=t)
                    RA, DEC = coordinates.ra.degree, coordinates.dec.degree
                if Target == "Moon":
                    coordinates = astropy.coordinates.get_moon(time=t)
                    RA, DEC = coordinates.ra.degree, coordinates.dec.degree
                if Target == "Zenith":
                    RA, DEC = "Zenith RA", "Zenith DEC"
                if Target == "Polaris":
                    RA, DEC = 37.9542, 89.26389
                self.Alignment_RA_Entry.insert(0, RA)
                self.Alignment_DEC_Entry.insert(0, DEC)
                self.Alignment_RA = RA
                self.Alignment_DEC = DEC

            except:
                self.Error("There occurred an error with choosing the option and inserting the Ra/Dec.")
            return

        def init_mount(self):
            '''
            This function connects the mount with the app. When the On/Off-Button is clicked this function is called.
            It changes the boolean self.active and updates the connection status as well as the look of the Button.
            :return: 
            Prints Error Message if Connection failed.
            '''
            if self.active:
                self.activation_button.config(bg='firebrick2')
                self.active_var.set('OFF')
                self.var_connection_status.set("Not Connected")
                self.active = False

            else:
                self.active = True
                print("Initialising to CGX mount...")
                self.var_connection_status.set("Connecting...")
                try:
                    self.cgx = NexStar(device=self.port)
                    print(self.cgx)
                    # self.sync_time_location()
                    self.cgx.sync(ra=0.0, dec=90.0)
                    self.update_RADEC()
                    self.activation_button.config(bg='PaleGreen2')
                    self.active_var.set('ON')
                    self.var_connection_status.set("Connected")
                    return
                except Exception as e:
                    self.activation_button.config(bg='firebrick2')
                    self.Error("Connection to Mount failed.")
                    self.active_var.set("OFF")
                    self.var_connection_status.set("Not Connected")
                    self.active = False
                    return

        def change_port(self, usb_port):
            '''
            This function will change the default port for the connection to the hand controller. It will also chaneg the status. 
            :param usb_port: Name of the usb_port input
            :return: 
            '''
            self.port = usb_port
            self.var_port.set("USB-Port: " + self.port)

        def update_RADEC(self):
            '''
            This function updates the Ra/Dec coordinates of the mount if the app is connected to the mount. 
            :return: 
            Prints Error if update failed.
            Prints "Mount is not connected" if the Mount is not connected.
            '''
            if self.active==True:
                try:
                    self.current_radec_var.set("RA: %f, DEC: %f" % self.cgx.get_radec())
                except:
                    self.Error("ERROR: Update RADEC")
            elif self.active==False:
                print("Mount is not connected")

        def LST(self):
            """
            Calculates local sidereal time based on location
            """
            t_utc = datetime.utcnow()
            YY = t_utc.year
            MM = t_utc.month
            DD = t_utc.day
            UT = t_utc.hour + (t_utc.minute / 60)
            JD = (367 * YY) - int((7 * (YY + int((MM + 9) / 12))) / 4) + int((275 * MM) / 9) + DD + 1721013.5 + (
                        UT / 24)
            GMST = 18.697374558 + 24.06570982441908 * (JD - 2451545)
            GMST = GMST % 24
            Long = self.location[1] / 15  # Convert longitude to hours
            LST = GMST + Long  # Fraction LST. If negative we want to add 24...
            if LST < 0:
                LST = LST + 24

            LSTmm = (LST - int(LST)) * 60  # convert fraction hours to minutes
            LSTss = (LSTmm - int(LSTmm)) * 60  # convert fractional minutes to seconds
            LSThh = int(LST)
            LSTmm = int(LSTmm)
            LSTss = int(LSTss)

            p = LST * 15

            return p

        def update_LST(self):
            '''
            Updates the LST Time 
            '''
            lst = self.LST() / 15
            LSTmm = (lst - int(lst)) * 60  # convert fraction hours to minutes
            LSTss = (LSTmm - int(LSTmm)) * 60  # convert fractional minutes to seconds
            LSThh = int(lst)
            LSTmm = int(LSTmm)
            LSTss = int(LSTss)
            self.sidereal_var.set('\nLocal Sidereal Time %s:%s:%s \n\n' % (LSThh, LSTmm, LSTss))
            self.after(1000, self.update_LST)

        def GoTo__RaDec(self, Ra, Dec):
            
            '''
            This function is used in the main window to Go To a specific set of Ra/Dec coordinates.
            :param Ra: Rigth Ascention Coordinate (ranges from -90 to +90)
            :param Dec: Declination Coordinate (ranges from -360 to +360)
            :return: 
            prints Error if Ra or Dec are too big.
            prints Error is Mount can not move to the given coorinates. 
            '''
            
            print('\nMount will move to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
            self.GoTo_RaDec_Status.set('\nMount is moving to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
            #mount moves
            try:
                assert (abs(float(Ra)) < 361 and abs(float(Dec)) < 91)
            except AssertionError:
                    print("Invalid RA or DEC")
                    self.GoTo_RaDec_InvalidRaDec_Message = "\nAssert that the total value of the RA < 360\n\nand that the total value of DEC < 90"
                    self.Error(self.GoTo_RaDec_InvalidRaDec_Message)
                    self.GoTo_RaDec_Status.set('\n --- \n\n' % (Ra, Dec))
                    return
            try:
                self.cgx.goto_radec(ra=float(Ra), dec=float(Dec))
                # mount moved
                print('\nMount has moved to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
                self.GoTo_RaDec_Status.set('\nMount has moved to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
            except:
                print("ERROR: GoTo_RaDec did not work")
                self.GoTo_RaDec_Error_Message = "\nMount was not able to move to given Ra/Dec coordinates\n"
                self.Error(self.GoTo_RaDec_Error_Message)
                self.GoTo_RaDec_Status.set('\n GoTo failed.\n\n' % (Ra, Dec))

        def GoTo_Alignment(self, Ra, Dec):
            '''
            Does the same as the GoTo__RaDec does but in the Alignment Tab.
            :param Ra: Right AscensionCoordinate (ranges from -90 to +90)
            :param Dec: Declination Coordinate (ranges from -360 to +360)
            :return: 
            prints Error if Ra or Dec are too big.
            prints Error is Mount can not move to the given coordinates
            '''
            print('\nMount will move to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
            self.Alignment_GoTo_LabelVar.set('\n --- \n')
            # mount moves
            try:
                assert abs(float(Ra)) < 361 and abs(float(Dec)) < 91
            except AssertionError:
                    print("Invalid RA or DEC")
                    self.GoTo_RaDec_InvalidRaDec_Message = "\nAssert that the total value of the RA < 360\n\nand that the total value of DEC < 90"
                    self.Error(self.GoTo_RaDec_InvalidRaDec_Message)
                    return

            try:
                self.cgx.goto_radec(ra=float(Ra), dec=float(Dec))
                # mount moved
                print('\nMount has moved to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
                self.Alignment_GoTo_LabelVar.set('\nMount has moved to (Ra:%s, Dec:%s) \n\n' % (Ra, Dec))
            except:
                print("GoTo_Alignment failed.")
                self.Error("Mount failed to move to the given coordinates. \n Check the Connection to the Mount.")

        def Abort_GoTo_RaDec(self):
            '''
            This function aborts the movement of the mount at any time. Can be used while slewing or while mount moves to a pair of coorinates.
            '''
            try:
                self.cgx.cancel_goto()
                self.after(10, self.update_RADEC)
                self.GoTo_RaDec_Status.set("Movement was aborted")
                return
            except:
                print("ERROR: Abort_GoTo_RaDec")
                self.Error("Abortion not possible. Check connection to Mount.")

        def Abort_GoTo_Alignment(self):
            '''
            This function aborts the movement of the mount at any time. Can be used while slewing or while mount moves to a pair of coorinates.
            '''
            try:
                self.cgx.cancel_goto()
                self.after(10, self.update_RADEC)
                self.Alignment_GoTo_LabelVar.set("Movement was aborted")
                print("Movement was aborted")
                return
            except:
                print("ERROR: Abort_GoTo_Alignment")
                self.Error("Abortion not possible. Check connection to Mount.")

        def set_slewrate(self, e):
            print(self.slewrate_var.get())

        def Alignment_set_slewrate(self, e):
            print("Slewrate for Alignment was chosen to be: %s" %(self.Alignment_slewrate_var.get()))

        def slew(self, ax, s):
            """
            The slewing function starts the movement of the mount in the direction of one axis with the speed s.
            When called again the funtion will stop the movement.
            :param ax(str): The mount axis to command. ('ra' or 'dec')
            :param s(float): The desired slew rate in arcseconds per second. Value may be positive or
                negative. The maximum rate is 16 000)
            """
            if self.slewing:
                rate = 0
                try:
                    self.cgx.slew_var(self.slewing_ax, rate)
                    print("stop slewing %s" % self.slewing_ax)
                    self.slewing = False
                except:
                    print("Slewing not possible to stop.")
                    self.Error("Slewing not possible to stop. Check if Mount is connected.")
            else:
                self.slewing_ax = ax
                rate = abs(int(self.slewrate_var.get()))
                try:
                    assert rate < 16000
                except AssertionError:
                    print("ERROR: Slewing rate to high")
                    self.Error("Assert that the Slewing Rate is < 16000")
                    return
                try:
                    self.cgx.slew_var(self.slewing_ax, s * rate)
                    print("slewing %s with rate %i" % (self.slewing_ax, s * rate))
                    self.slewing = True
                except:
                    self.Error("Slewing not possible. Check if Mount is connected.")

            return

        def Alignment_slew(self, ax, s):
            """
            The slewing function starts the movement of the mount in the direction of one axis with the speed s.
            When called again the funtion will stop the movement.
            :param ax(str): The mount axis to command. ('ra' or 'dec')
            :param s(float): The desired slew rate in arcseconds per second. Value may be positive or
                            negative. The maximum rate is 16 000)
            """

            if self.slewing:
                rate = 0
                try:
                    self.cgx.slew_var(self.slewing_ax, 0)
                    print("stop slewing %s" % self.slewing_ax)
                    self.slewing = False
                except:
                    print("Slewing not possible to stop.")
                    self.Error("Slewing not possible to stop. Check if Mount is connected.")

            else:
                self.slewing_ax = ax
                rate = abs(int(self.Alignment_slewrate_var.get()))
                try:
                    assert rate < 16000
                except AssertionError:
                    print("ERROR: Slewing rate to high")
                    self.Error("Assert that the Slewing Rate is < 16000")
                    return
                try:
                    self.cgx.slew_var(self.slewing_ax, s * rate)
                    print("slewing %s with rate %i" % (self.slewing_ax, s * rate))
                    self.slewing = True
                except:
                    self.Error("Slewing not possible. Check if Mount is connected.")
            return

        def Synchronize(self, Ra, Dec):
            '''
            The Telescope Hand Controller will get the information that the current position of the mount is
            alligned with the given set of Ra/Dec coordinates.
            '''
            try:
                self.cgx.sync(float(Ra), float(Dec))
                self.Message("Telescope synchronised.")
            except:
                print("Error: Synchronize did not work")
                self.Error("\nSynchronization did not work.\n")

        def Measure(self):
            x=1
            self.Message("Measuring...")
            #Do here fancy Measurement Programm
            #Pop Up Plots
            #Save All Data

        def calculate_coordinates_measurement(self, filename):
            """
            This function calculates the coordinates for the Measurements in Ra Dec Coordinates and opens a csv file
            Long1, Lat1 = Start Galactic Coordinates
            Long2, Lat2 = End Galactic Coordinates
            Num = Number of Measurements

            :return:

            """
            try:
                Long1, Long2 = float(self.GalLong1_Entry.get()), float(self.GalLong2_Entry.get())
                Lat1, Lat2 = float(self.GalLat1_Entry.get()), float(self.GalLat2_Entry.get())
                Num = int(self.NumMeasurments_Entry.get())
                assert Long1 < 180 and Long2 < 180 and abs(Lat1) < 91 and abs(Lat2) < 91
                assert Num > 1
            except:
                self.Error("Invalid Input")

            Start_Coordinates = SkyCoord(Long1*u.deg, Lat1*u.deg, frame="galactic")
            Stop_Coordinates = SkyCoord(Long2*u.deg, Lat2*u.deg, frame="galactic")


            Start_Coordinates_RaDec = Start_Coordinates.transform_to('icrs')
            Stop_Coordinates_RaDec = Stop_Coordinates.transform_to('icrs')
            Dif_Ra = (Start_Coordinates_RaDec.ra - Stop_Coordinates_RaDec.ra)/(Num-1)
            Dif_Dec = (Start_Coordinates_RaDec.dec - Stop_Coordinates_RaDec.dec)/(Num-1)

            Ra_Cord, Dec_Cord, index = [], [], []

            for i in range(Num):
                index.append(i)
                Ra_Cord.append(((Start_Coordinates_RaDec.ra - i*Dif_Ra)*u.deg).value)
                Dec_Cord.append(((Start_Coordinates_RaDec.dec - i*Dif_Dec)*u.deg).value)

            csv_file = open(filename,"w", newline="")
            wr = csv.writer(csv_file)
            wr.writerow(["Name", "RA", "DEC"])
            bla = [index, Ra_Cord, Dec_Cord]
            wr.writerows(zip(*bla))
            csv_file.close()
            print("CSV file " + filename + " was created")
            int(Ra_Cord[0])

        def open_csv(self, name_file):
            '''
            This funtcion opens the file with the path name_file with webbrowser if possible.
            If not an Error Message is displayed.
            '''
            try:
                self.MessageInMessageFrame = "If you want to start the measurment from the file\n'" + self.Open_csv_filename_Entry.get() + "'\npress the 'Start Measurment'-Button."
                self.Measurment_Frame_2_LabelVar3.set(self.MessageInMessageFrame)
                subprocess.call(['open', name_file])
                print("Opening file " + name_file)
            except:
                self.Error("It was not possible to open the file.")

        def MessageInMessageFrame_update(self, event):
            self.Measurment_Frame_2_LabelVar3.set("If you want to start the measurment from the file\n'" + self.Open_csv_filename_Entry.get() + "'\npress the 'Start Measurment'-Button.")

        def MilkyWayGalaxy_Measurment(self, filename):
            '''
            This function will open and read the filename file and then start the measurment, for each set of coordinates.
            :param filename: name of the csv-file which should contain the coordinates
            '''

            csv_file = open(filename,"r", newline="")
            print("Reading file " + filename)
            n = 0
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                self.Message("The program will now start the measurement of  " + row["Name"] +"; the coordinates are RA: " + row["RA"]  + ", DEC: " + row["DEC"]  +
                             ".\n  Press okay to continue.")
                try:
                    Name, RA, Dec = row["Name"], row["RA"], row["DEC"]
                    Ra_coord, Dec_coord = float(RA), float(Dec)
                except:
                    self.Error("File could not be read. Error occurred at row #" + str(num))
                try:
                    #self.GoTo__RaDec(Ra_coord, Dec_coord)
                    #time.sleep(10)
                    self.Measure()
                    #time.sleep(10)
                except:
                    self.Error("Measurment failed. Error occured at row #" + str(num))
                n = n + 1
            csv_file.close()
            return 0

        def Error(self, Message):
            '''
            This function prints an Error Message in the Terminal and Also gives an Error Message in a Messagebox of Tkinter.
            :param Message: The Message which should be printed
            '''
            tkinter.messagebox.showerror("Error", Message)
            print(Message)

        def Message(self, Message):
            tkinter.messagebox.showinfo(title=None, message=Message)
            print(Message)

HEIGHT = 900
WIDTH = 1100


#creat tk
root = Tk()
root.wm_title("CGXL mount control")

canvas = Canvas(root, height=HEIGHT, width=WIDTH)
canvas.pack()

#creat window

app = Window(root)

root.mainloop()