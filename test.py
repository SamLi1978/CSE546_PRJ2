
'''

Mode    Description	                        File Pointer Position	Creates File if Not Exists	Truncates Existing File
r	    Read-only	                        Beginning of the file	No	                        No
r+	    Read and write (updating)	        Beginning of the file	No	                        No
w	    Write-only (overwrite or create)	Beginning of the file	Yes	                        Yes
w+	Write and read (overwrite or create)	Beginning of the file	Yes	                        Yes
a	Append-only (append or create)	        End of the file	        Yes	                        No
a+	Append and read (append or create)	    End of the file	        Yes	                        No

'''


import configparser
import os

image_result_ini = 'image_result.ini'
image_result_section = 'image_result'

def image_result_set_data(key, value):

    if not os.path.exists(image_result_ini):
        with open(image_result_ini, 'w') as ini:
            pass

    config = configparser.ConfigParser()

    '''
    config.read('test.ini')
    or 
    with open(image_result_ini, 'r') as ini:
        config.read_file(ini)

    Both of them make the ini file appendable, or the ini file will be rewritten.
    '''
    with open(image_result_ini, 'r') as ini:
        config.read_file(ini)
 
    if config.has_section(image_result_section) == False:
        config.add_section(image_result_section)    
    
    config.set(image_result_section, key, value)

    with open(image_result_ini, 'w') as ini:
        config.write(ini)



if __name__ == "__main__":

    image_result_set_data('test_12.JPEG', 'shitshit')

