import socket
import os
import sys

def send_file_to_server(file_path, host="127.0.0.1", port=12345):
    """
    Отправляет текстовый файл на сервер.
    Сначала отправляет размер файла (4 байта), затем содержимое.
    """
    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"Ошибка: файл '{file_path}' не найден!")
        return False
    
    # Читаем содержимое файла
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return False
    
    # Создаем сокет и подключаемся
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        
        print(f"Отправка файла '{file_path}' на сервер {host}:{port}")
        
        # Кодируем содержимое в байты
        data_bytes = file_content.encode("utf-8")
        data_size = len(data_bytes)
        print(f"Размер данных: {data_size} байт")
        
        # Сначала отправляем размер данных (4 байта, big-endian)
        client_socket.send(data_size.to_bytes(4, byteorder='big'))
        
        # Затем отправляем сами данные
        client_socket.send(data_bytes)
        
        # Получаем ответ от сервера
        response = client_socket.recv(1024).decode("utf-8")
        print(f"Ответ сервера: {response}")
        
        return "OK" in response
        
    except ConnectionRefusedError:
        print("Ошибка: Сервер недоступен. Убедитесь, что сервер запущен.")
        return False
    except Exception as e:
        print(f"Ошибка при отправке: {e}")
        return False
    finally:
        client_socket.close()

def main():
    print("=== КЛИЕНТ ДЛЯ ОТПРАВКИ ФАЙЛОВ НА СЕРВЕР ===")
    
    if len(sys.argv) > 1:
        # Если файл передан как аргумент командной строки
        file_path = sys.argv[1]
        send_file_to_server(file_path)
    else:
        # Интерактивный режим
        while True:
            print("\n1. Отправить файл")
            print("2. Выход")
            choice = input("Выберите действие: ")
            
            if choice == "1":
                file_path = input("Введите путь к текстовому файлу: ")
                send_file_to_server(file_path)
            elif choice == "2":
                print("До свидания!")
                break
            else:
                print("Неверный выбор!")

if __name__ == "__main__":
    main()