@echo off
rem WARNING: This batch file DELETES files. Run at your own risk.

cls

if exist test-out\*.nes del test-out\*.nes

echo === These should cause five errors ===
python nes_color_swap.py nonexistent test-out\temp1.nes
python nes_color_swap.py test-in\smb1.nes test-in\smb1.nes
python nes_color_swap.py --first-tile 9999 test-in\smb1.nes test-out\temp2.nes
python nes_color_swap.py --tile-count 9999 test-in\smb1.nes test-out\temp3.nes
python nes_color_swap.py test-in\invalid-id.nes test-out\temp4.nes
echo.

if exist test-out\*.nes del test-out\*.nes

echo === Swapping colors ===
python nes_color_swap.py test-in\smb1.nes test-out\smb-default_settings.nes

python nes_color_swap.py --color0 0 --color1 1 --color2 2 --color3 3 test-in\smb1.nes test-out\smb1-colors0123.nes
python nes_color_swap.py --color0 0 --color1 2 --color2 3 --color3 1 test-in\smb1.nes test-out\smb1-colors0231.nes
python nes_color_swap.py --color0 0 --color1 3 --color2 1 --color3 2 test-in\smb1.nes test-out\smb1-colors0312.nes
python nes_color_swap.py --color0 1 --color1 2 --color2 3 --color3 2 test-in\smb1.nes test-out\smb1-colors1232.nes

python nes_color_swap.py -0 1 -1 2 -2 3 -3 0 --tile-count 1 test-in\smb1.nes test-out\smb1-tile_0_only.nes
python nes_color_swap.py -0 1 -1 2 -2 3 -3 0 --first-tile 1 --tile-count 1 test-in\smb1.nes test-out\smb1-tile_1_only.nes
python nes_color_swap.py -0 1 -1 2 -2 3 -3 0 --first-tile 511 test-in\smb1.nes test-out\smb1-tile_511_only.nes

python nes_color_swap.py test-in\blastermaster.nes test-out\blastermaster-colors0231.nes
python nes_color_swap.py -0 0 -1 1 -2 2 -3 3 test-in\blastermaster.nes test-out\blastermaster-colors0123.nes
echo.

echo === Comparing (should be identical) ===
fc /b test-in\smb1.nes test-out\smb1-colors0123.nes
fc /b test-in\blastermaster.nes test-out\blastermaster-colors0123.nes

echo === Comparing (only tile 0/1/511 changed) ===
fc /b test-in\smb1.nes test-out\smb1-tile_0_only.nes
fc /b test-in\smb1.nes test-out\smb1-tile_1_only.nes
fc /b test-in\smb1.nes test-out\smb1-tile_511_only.nes
echo.

echo === Look at the files under test-out\ yourself ===
