import io


def read_text_file(uploaded_file):
    """
    读取 Streamlit 的 UploadedFile 对象并返回字符串
    """
    if uploaded_file is None:
        return ""

    # 获取文件扩展名
    file_type = uploaded_file.name.split('.')[-1].lower()

    if file_type == 'txt':
        # 读取 TXT
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        return stringio.read()

    elif file_type == 'pdf':
        # TODO: 如果需要支持 PDF，需要安装 PyPDF2
        # import PyPDF2
        # reader = PyPDF2.PdfReader(uploaded_file)
        # text = ""
        # for page in reader.pages:
        #     text += page.extract_text() + "\n"
        # return text
        return "[暂不支持 PDF 解析，请上传 TXT]"

    return ""