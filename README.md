# Mediavida Old Posts Remover

Un script de Python para automatizar la edición y limpieza de posts antiguos en los foros de Mediavida.com.
Solo elimina los posts listados en tu perfil.

Esta herramienta te permite iniciar sesión en tu cuenta y reemplazar el contenido de todos los posts que superen una antigüedad determinada (definida en años) por un simple punto (`.`).

## Características Principales

* **Inicio de sesión automático**: Se conecta a tu cuenta de Mediavida de forma segura.
* **Búsqueda Binaria Eficiente**: En lugar de escanear todas tus páginas de posts una por una, utiliza un algoritmo de búsqueda binaria para localizar rápidamente la primera página que contiene posts antiguos. Esto ahorra una cantidad significativa de tiempo, especialmente para usuarios con un gran historial de mensajes.
* **Edición Selectiva por Antigüedad**: Solo modifica los posts que son más antiguos que el número de años que especifiques.
* **Optimización de Tráfico**:
    * **Comprobación de Contenido**: Antes de realizar una edición, el script verifica si el contenido del post ya es un ".". Si es así, lo omite para evitar peticiones innecesarias.
    * **Registro de Actividad**: Crea y mantiene un archivo `edited_posts.txt` para guardar las URLs de todos los posts ya procesados (tanto los editados como los omitidos). En ejecuciones futuras, el script no volverá a procesar estos posts, acelerando aún más el proceso.
* **Manejo Seguro de Credenciales**: Tu contraseña se introduce de forma segura en la terminal sin que se muestre en pantalla, gracias a la librería `getpass`.

## Uso

1.  **Clona o descarga el repositorio.**
2.  **Instala las dependencias necesarias** a través de la terminal:
    ```bash
    pip install requests beautifulsoup4 python-dateutil
    ```
3.  **Ejecuta el script** desde la misma terminal:
    ```bash
    python mediavida_old_posts_remover.py
    ```
4.  **Sigue las instrucciones en pantalla**:
    * Introduce tu nombre de usuario.
    * Introduce tu contraseña (no será visible).
    * Especifica la antigüedad en años (por ejemplo, `15` para editar todo lo que tenga más de 15 años).
    * Confirma la operación antes de que comience la edición.

## ⚠️ Advertencia Importante

**¡Uso bajo tu propia responsabilidad!**

Este script realiza cambios **permanentes e irreversibles** en tus posts de Mediavida. No hay forma de recuperar el contenido original una vez que ha sido reemplazado.

Asegúrate de entender completamente lo que hace el código antes de ejecutarlo. El autor no se hace responsable de ninguna pérdida de datos, suspensión de la cuenta o cualquier otro problema derivado del uso de esta herramienta.
