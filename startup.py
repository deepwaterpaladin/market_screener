import subprocess
import sys

def install_dependencies() -> None:
    """
    Install dependencies listed in requirements.txt using pip.

    Raises:
        subprocess.CalledProcessError: If an error occurs during the installation process.
    """
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Error occurred while installing dependencies.")

def setup_jupyter() -> None:
    """
    Set up Jupyter Notebook and configure a kernel for the environment.

    Raises:
        subprocess.CalledProcessError: If an error occurs during the setup process.
    """
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', 'jupyter'])
        subprocess.check_call([sys.executable, '-m', 'ipykernel', 'install',
                              '--user', '--name', 'env', '--display-name', 'Python (env)'])
        print("Jupyter setup completed successfully.")
    except subprocess.CalledProcessError:
        print("Error occurred while setting up Jupyter.")

def create_env_file() -> None:
    """
    Create a .env file if it doesn't exist.

    Writes:
        A new .env file with a placeholder message.
    """
    try:
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("FMP_KEY_1 = # *** YOUR API KEY *** ")
            print(".env file created.")
        else:
            print(".env file already exists")
    except:
        print("Unable to add .env file")


if __name__ == "__main__":
    install_dependencies()
    setup_jupyter()
    create_env_file()
