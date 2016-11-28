import os
import tinys3
import logging
from PIL import Image


def save_htmls_screenshots(folder, driver, filename, screenshots_conf):

    def crop_height_img(fullpath, max_heigh=1800):
        """ Recorta la imagen a lo largo """
        img = Image.open(fullpath)
        if img.height > max_heigh:
            img = img.crop((0, 0, img.width, max_heigh)) # para que grafana pueda pintarla bien.
        img.save(fullpath)

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
    
    path = screenshots_conf["SCREEN_LOG_PATH"]+"/"+folder
    if not os.path.exists(path): os.makedirs(path)
    
    dir_size = size_of_dir(path)
    if dir_size>=screenshots_conf["MAX_DIR_SIZE"]:
        clear_dir(path)

    try:
        fullpath = os.path.join(path, "%s.png" % filename)
        driver.save_screenshot(fullpath)
        # Recortamos la imagen a lo largo para una correcta visualizacion en grafana
        crop_height_img(fullpath)
    except Exception as ex:
        logging.warning("No se ha podido guardar el screenshot '%s/%s.png' :\n %s" % (path, filename, ex))
    else:
        if screenshots_conf.get("BUCKET_NAME"):
            push_file_to_s3("%s.png" % filename, path, folder, screenshots_conf)
    try:
        html_path = os.path.join(path, "%s.html" % filename)
        with open(html_path, "wb") as f:
            f.write(driver.page_source.encode('utf-8'))
    except Exception as ex:
        logging.warning("No se ha podido guardar el screenshot '%s/%s.html':\n%s" % (path, filename, ex))
    else:
        if screenshots_conf.get("BUCKET_NAME"):
            push_file_to_s3("%s.html" % filename, path, folder, screenshots_conf)


def push_file_to_s3(filename, filepath, s3_folder, screenshots_conf):
    f = None
    fullpath = "%s/%s" % (filepath, filename)
    try:
        f = open(fullpath, "rb")
    except IOError as e:
        logging.error("No se ha podido subir el archivo para subirlo a S3, posiblemente no se ha guardado: \n%s" % e)
    if f:
        try:
            conn = tinys3.Connection(screenshots_conf["AWS_ACCESS_KEY_ID"],
                screenshots_conf["AWS_SECRET_ACCESS_KEY"],
                endpoint=screenshots_conf["ENDPOINT"])
            conn.upload("%s/%s" % (s3_folder, filename), f, screenshots_conf["BUCKET_NAME"])
            print "%s/%s" % (s3_folder, filename)
            f.close()
        except Exception as e:
            f.close()
            logging.error("error subiendo archivo a S3: \n%s" % e)
        else:            
            os.remove(fullpath)




