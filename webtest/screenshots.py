import os
import tinys3
import logging

# SCREEN_LOG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../screenshots"
#TODO: Extraer la definicion de la variable SCREEN_LOG_PATH?
# SCREEN_LOG_PATH = "/opt/wachiman/screenshots"
# SCREEN_LOG_PATH = "/home/tolo/projects/wachiman/screenshots"
SCREEN_LOG_PATH = os.getenv("SCREEN_LOG_PATH")
MAX_DIR_SIZE = os.getenv("MAX_DIR_SIZE", 50) #mb

#TODO: Sacar las siguientes variables de S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID") 
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
ENDPOINT = os.getenv("ENDPOINT")

def save_htmls_screenshots(folder, driver, filename, push_to_s3 = False):

    def size_of_dir(dirname):
        """Walks through the directory, getting the cumulative size of the directory"""
        suma = 0
        files_names = os.listdir(dirname)
        for file in files_names:
            suma += os.path.getsize(dirname+"/"+file)
        kilobytes = suma/1024
        return kilobytes/1024 #megabytes

    def clear_dir(path):
        """ borra una tercera parte de los archivos """
        files_paths = []
        for filename in os.listdir(path):
            files_paths.append(path + "/" + filename)
        sorted_files = sorted(files_paths, key=lambda filepath: os.stat(filepath).st_mtime)
        for file_path in sorted_files[0:len(sorted_files)/3]:
            os.remove(file_path)
    
    path = SCREEN_LOG_PATH+"/"+folder
    if not os.path.exists(path): os.makedirs(path)
    
    dir_size = size_of_dir(path)
    if dir_size>=MAX_DIR_SIZE:
        clear_dir(path)

    try:
        driver.save_screenshot(os.path.join(path, "%s.png" % filename))
    except Exception as ex:
        logging.warning("No se ha podido guardar el screenshot '%s/%s.png' :\n %s" % (path, filename, ex))
    else:
        if push_to_s3: push_file_to_s3("%s.png" % filename, path, folder)
    try:
        html_path = os.path.join(path, "%s.html" % filename)
        with open(html_path, "wb") as f:
            f.write(driver.page_source.encode('utf-8'))
    except Exception as ex:
        logging.warning("No se ha podido guardar el screenshot '%s/%s.html':\n%s" % (path, filename, ex))
    else:
        if push_to_s3: push_file_to_s3("%s.html" % filename, path, folder)


def push_file_to_s3(filename, filepath, s3_folder):
    f = None
    try:
        fullpath = "%s/%s" % (filepath, filename)
        f = open(fullpath, "rb")
    except IOError as e:
        logging.error("No se ha podido subir el archivo para subirlo a S3, posiblemente no se ha guardado: \n%s" % e)
    if f:
        try:
            conn = tinys3.Connection(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY, endpoint=ENDPOINT)
            conn.upload("%s/%s" % (s3_folder, filename), f, BUCKET_NAME)
            f.close()
        except Exception as e:
            f.close()
            logging.error("error subiendo archivo a S3: \n%s" % e)
        else:            
            os.remove(fullpath)




