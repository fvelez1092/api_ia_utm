# Template_API-flask
Plantilla para la creación y posterior desarrollo de APIs REST en Flask (Python).

## Indice

* [Creación de un Entorno Virtual](#creación-de-un-entorno-virtual)
  * [Opciones de creación de entornos virtuales](#opciones-de-creación-de-entornos-virtuales)
* [Variables de Entorno](#variables-de-entorno)
  * [Ejemplo de un archivo .env](#ejemplo-de-un-archivo-.env)
* [Generación de Par de Claves (Privada y Pública)](#generación-de-par-de-claves-(privada-y-pública))
  * [Generar una clave RSA de 2048 bits](#generar-una-clave-RSA-de-2048-bits)
  * [Exportar la clave pública RSA a un archivo](#exportar-la-clave-pública-RSA-a-un-archivo)
* [Despliegue del API](#despliegue-del-api)

## Creación de un Entorno Virtual

Para crear un entorno virtual usando pipenv, siga estos pasos:

Instale pipenv si aún no lo ha hecho:
```pip install pipenv```

Cree un directorio para su proyecto:
```
mkdir my_project
cd my_project
```

Inicie un entorno virtual:
```
pipenv install
```
Esto creará un entorno virtual llamado my_project en la carpeta .venv.

Para iniciar el entorno virtual, ejecute el siguiente comando:

```
pipenv shell
```
Esto cambiará a la shell del entorno virtual.

Para instalar paquetes en el entorno virtual, use el comando pipenv install:

```
pipenv install requests
```
Esto instalará el paquete requests en el entorno virtual.

Para salir del entorno virtual, ejecute el siguiente comando:

```
exit
```
### Opciones de creación de entornos virtuales

Pipenv ofrece varias opciones para crear entornos virtuales, como:

Especificar la versión de Python:
```
pipenv install --python 3.9
```
Esto creará un entorno virtual con Python 3.10.

Especificar el nombre del entorno virtual:
```
pipenv install --name my_env
```
Esto creará un entorno virtual llamado my_env.

Especificar las dependencias:
```
pipenv install requests django
```
Esto instalará los paquetes requests y django en el entorno virtual.

### Recomendaciones

Se recomienda crear un entorno virtual para cada proyecto de Python. Esto ayudará a aislar las dependencias de cada proyecto y evitará conflictos.

------

## Variables de Entorno
Variables de entorno básicas para la ejecución del Proyecto:

+ *ENVIRONMENT*: Define el tipo de Entorno en el que se ejecuta el Proyecto. Ejem. DEV -> Desarrollo | PRO -> Producción
+ [*SECRET_KEY*](https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY): Una clave secreta que se utilizará para firmar de forma segura la cookie de sesión y que las extensiones o su aplicación pueden utilizar para cualquier otra necesidad relacionada con la seguridad. Debe ser una cadena o bytes aleatorios largos.
+ [*DEV_DATABASE_URI*](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/config/#flask_sqlalchemy.config.SQLALCHEMY_DATABASE_URI): El URI de conexión de la base de datos de **Desarrollo** utilizado para el motor predeterminado. Puede ser una cadena o una instancia de URL de SQLAlchemy.
+ [*PROD_DATABASE_URI*](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/config/#flask_sqlalchemy.config.SQLALCHEMY_DATABASE_URI): El URI de conexión de la base de datos de **Producción** utilizado para el motor predeterminado. Puede ser una cadena o una instancia de URL de SQLAlchemy.
+ [*JWT_SECRET_KEY*](https://flask-jwt-extended.readthedocs.io/en/stable/options.html#jwt-secret-key): La clave secreta utilizada para codificar y descodificar JWTs cuando se utiliza un algoritmo de firma simétrico (como HS). Debe ser una cadena larga aleatoria de bytes, aunque también se acepta unicode.
+ [*JWT_ALGORITHM*](https://flask-jwt-extended.readthedocs.io/en/stable/options.html#JWT_ALGORITHM): Con qué algoritmo firmar el JWT. Ver [PyJWT](https://pyjwt.readthedocs.io/en/latest/algorithms.html) para los algoritmos disponibles.

### Ejemplo de un archivo .env
```
ENVIRONMENT="DEV"
SECRET_KEY="SUPER_SECRET_KEY"
DEV_DATABASE_URI="postgresql+psycopg2://postgres:password@localhost:5432/template_flask"
PROD_DATABASE_URI=""
JWT_SECRET_KEY="SUPER_SECRET_KEY"
JWT_ALGORITHM="RS256"
CHROMA_PATH="./chroma_db" 
COLLECTION_NAME="gadpm_documents"
OLLAMA_HOST = "http://172.20.51.50:11434"
EMBEDDING_MODEL="model-elaia-mistral"
```


> [!IMPORTANT]
> Recuerda siempre cambiar la *SECRET_KEY* y *JWT_SECRET_KEY* por un Hash distinto para la implementación en Producción.
> 
> Además de no revelar dicho Hash de producción en el repositorio de Git.

------

## [Generación de Par de Claves (Privada y Pública) con OpenSSL](https://github.com/NicoSan13/Template_API-flask/files/13561466/generating_rsa_key_from_command.pdf)

Encriptación de archivos con criptografía de clave pública

#### Generar una clave RSA de 2048 bits

Para generar un par de claves RSA pública y privada se usa el siguiente comando:

```
openssl genrsa -des3 -out private.pem 2048
```

Esto genera un par de claves RSA de 2048 bits, las encripta con la contraseña que se ingresó y las escribe en un archivo. A continuación, se necesita extraer el archivo de clave pública. 

#### Exportar la clave pública RSA a un archivo

Para exportarla se usa el siguiente comando:

```
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
```

A continuación, abra el archivo public.pem y asegúrese de que comience con ```-----BEGIN PUBLIC KEY-----```. Así es como sabe que este archivo es la clave pública del par y no una clave privada.

Para verificar el archivo desde la línea de comandos, puede usar el comando ```less```:

```less public.pem```

Al generar la Clave Privada, esta se genera encriptada. Para poder utilizarla con la libreria Flask_JWT se debe de desencriptar ya que [no cuenta con soporte para decodificar Claves Privada con passphrases](https://github.com/jpadilla/pyjwt/pull/199#issuecomment-325068235).

Para ello se debe usar el siguiente comando:

```openssl rsa -in private_key.pem -out private_dec_key.pem```

El archivo PEM resultante debe ser cargado como Clave Privada.

[Referencia de comandos CLI Open SSL](https://wiki.openssl.org/index.php/Command_Line_Utilities)

[Referencia de la Guia para generar el par de Claves RSA](https://rietta.com/blog/openssl-generating-rsa-key-from-command/)

------

## Despliegue del API

Para desplegar el API de Flask, primero debes de asegurarte que te encuentres dentro del Entorno Virtual (pipenv).

# Coming Soon....
