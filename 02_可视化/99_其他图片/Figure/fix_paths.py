import os
import re
import glob

png_dir = r'D:\system_folder\Desktop\Work On\02_可视化\Figure\png'
root_old = r'D:\system_folder\Desktop\Work On'
root_new = r'D:\system_folder\Desktop\Work On'

for py_file in glob.glob('*.py'):
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace root paths
    content = content.replace(root_old, root_new)
    content = content.replace(root_old.replace('\\', '\\\\'), root_new.replace('\\', '\\\\'))
    
    # Overwrite OUT_DIR if it exists, or anything plotting to OUT_DIR
    # We can try to replace any saving directory with png_dir
    content = re.sub(r'OUT_DIR\s*=\s*r?[\'\"][^\'\"]+[\'\"]', f'OUT_DIR = r"{png_dir}"', content)
    
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Paths updated in py files')
