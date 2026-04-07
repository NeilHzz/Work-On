import os
import pandas as pd
from Bio.PDB import *
from Bio.PDB.SASA import ShrakeRupley

def calculate_sasa_for_structure(pdb_file, probe_radius):
    """计算给定PDB文件的SASA，包括蛋白质和糖链"""
    parser = PDBParser()
    try:
        structure = parser.get_structure('protein', pdb_file)
        sr = ShrakeRupley(probe_radius=probe_radius)
        sr.compute(structure, level="R")  # 计算残基级别的SASA
        
        # 分别计算蛋白质和糖链的SASA
        protein_sasa = 0
        glycan_sasa = 0
        
        for model in structure:
            for chain in model:
                for residue in chain:
                    res_sasa = sum(atom.sasa for atom in residue)
                    # HETATM记录通常用于糖链和其他非标准残基
                    if residue.id[0].strip():  # 如果residue.id[0]不是空字符串，说明是HETATM
                        glycan_sasa += res_sasa
                    else:
                        protein_sasa += res_sasa
                        
        return {
            'total_sasa': protein_sasa + glycan_sasa,
            'protein_sasa': protein_sasa,
            'glycan_sasa': glycan_sasa
        }
    except Exception as e:
        print(f"处理文件 {pdb_file} 时出错: {str(e)}")
        return None

def main():
    # 设置目录路径
    directory = r"E:\Data\Desktop\Work On\ReGlyco"
    
    # 存储结果的列表
    results = []
    
    # 遍历目录中的所有PDB文件
    for filename in os.listdir(directory):
        if filename.endswith('.pdb'):
            pdb_path = os.path.join(directory, filename)
            
            # 使用两个不同的探针半径计算SASA
            sasa_1_0 = calculate_sasa_for_structure(pdb_path, 1.0)
            sasa_3_5 = calculate_sasa_for_structure(pdb_path, 3.5)
            
            if sasa_1_0 and sasa_3_5:  # 确保计算成功
                results.append({
                    'PDB文件': filename,
                    'Total SASA (r=1.0)': sasa_1_0['total_sasa'],
                    'Protein SASA (r=1.0)': sasa_1_0['protein_sasa'],
                    'Glycan SASA (r=1.0)': sasa_1_0['glycan_sasa'],
                    'Total SASA (r=3.5)': sasa_3_5['total_sasa'],
                    'Protein SASA (r=3.5)': sasa_3_5['protein_sasa'],
                    'Glycan SASA (r=3.5)': sasa_3_5['glycan_sasa']
                })
    
    # 创建DataFrame并保存到Excel
    df = pd.DataFrame(results)
    output_file = r"E:\Data\Desktop\Work On\sasa_results.xlsx"
    df.to_excel(output_file, index=False)
    print(f"计算完成！结果已保存到: {output_file}")

if __name__ == "__main__":
    main()