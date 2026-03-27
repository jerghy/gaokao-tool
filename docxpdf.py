import os
import time
import pythoncom
import win32com.client

def convert_word_to_pdf_recursive(root_folder):
    if not os.path.isdir(root_folder):
        print(f"错误：文件夹不存在 → {root_folder}")
        return

    print(f"开始递归扫描并转换 → {root_folder}\n")

    word_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            lower_name = filename.lower()
            if (lower_name.endswith(".docx") or lower_name.endswith(".doc")) and not filename.startswith("~$"):
                word_files.append(os.path.join(dirpath, filename))

    if not word_files:
        print("未找到任何 .doc 或 .docx 文件")
        return

    word = None
    success_count = 0
    fail_count = 0
    skip_count = 0

    try:
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = True
        word.DisplayAlerts = 0

        for i, word_file in enumerate(word_files, 1):
            pdf_file = os.path.splitext(word_file)[0] + ".pdf"
            print(f"[{i}/{len(word_files)}] {os.path.basename(word_file)}", end=" ")

            if os.path.exists(pdf_file):
                print("→ PDF已存在，跳过")
                skip_count += 1
                continue

            success = False
            for retry in range(3):
                doc = None
                try:
                    abs_word = os.path.abspath(word_file)
                    abs_pdf = os.path.abspath(pdf_file)
                    
                    doc = word.Documents.Open(abs_word, ReadOnly=True)
                    doc.SaveAs(abs_pdf, FileFormat=17)
                    doc.Close(False)
                    success = True
                    break
                except Exception as e:
                    if doc:
                        try:
                            doc.Close(False)
                        except:
                            pass
                    if retry < 2:
                        time.sleep(2)
                    else:
                        print(f"❌ {str(e)[:50]}")
                        fail_count += 1

            if success:
                print("✅")
                success_count += 1

        print(f"\n完成！成功: {success_count}, 跳过: {skip_count}, 失败: {fail_count}")

    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
    finally:
        if word:
            try:
                word.Quit()
            except:
                pass
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    target_folder = r"D:\学习\2024版.新高考新教材版.选考总复习.化学.5·3B版"
    convert_word_to_pdf_recursive(target_folder)
