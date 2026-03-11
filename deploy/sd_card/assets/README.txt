Place external runtime assets here.

Preferred deployment location on hardware:
- /sd/assets

Supported files currently:
- backgrounds/*.bmp (24-bit BMP, 128x160 recommended)
- sprites/recruits/*.bmp (24-bit BMP, 16x24 recommended)

Background filenames used by scene:
- save_slots.bmp
- guild_hall.bmp
- roster.bmp
- tavern.bmp
- recruit.bmp
- missions.bmp
- training.bmp
- settings.bmp
- log.bmp

Recruit sprite lookup order:
1) sprites/recruits/<recruit_id>.bmp
2) sprites/recruits/class_<job_class>.bmp
3) sprites/recruits/race_<race>.bmp
4) sprites/recruits/default.bmp
