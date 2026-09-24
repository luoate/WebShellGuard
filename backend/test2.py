import hashlib

def calculate_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        chunk = file.read(8192)
        while chunk:
            md5.update(chunk)
            chunk = file.read(8192)
    return md5.hexdigest()

if __name__ == "__main__":
    md5_value = calculate_md5("C:\\Users\\lowi\\PycharmProjects\\MSDetector-master\\model\\train\\第四次测试.pth")
    print(f"文件的MD5值是: {md5_value}")
    md5_value = calculate_md5("C:\\Users\\lowi\\PycharmProjects\\MSDetector-master\\model\\train\\第五次测试.pth")
    print(f"文件的MD5值是: {md5_value}")
    md5_value = calculate_md5("C:\\Users\\lowi\\PycharmProjects\\MSDetector-master\\model\\train\\第三次测试.pth")
    print(f"文件的MD5值是: {md5_value}")
