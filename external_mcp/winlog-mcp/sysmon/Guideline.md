# User Installation and Operation Guide

- **Table of Contents**
    - [1. Environment Setup](#1-environment-setup)
        - [1.1 Installing PowerShell](#11-installing-powershell)
        - [1.2 Installing Python](#12-installing-python)
    - [2. Usage Instructions](#2-usage-instructions)
        - [2.1 How to Set Up the Extraction Environment](#21-how-to-set-up-the-extraction-environment)
        - [2.2 How to Use the Upload Service](#22-how-to-use-the-upload-service)
    - [FAQ](#faq)

## 1. Environment Setup

Before using this service, please ensure the following environments are installed:

- [PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4)
- [Python](https://www.python.org/downloads/)

### 1.1 Installing PowerShell

According to Microsoft’s official documentation, there are several ways to install PowerShell on Windows:

- **Method 1:** Install PowerShell using Winget (Recommended)

    ```cmd
    winget search Microsoft.PowerShell
    ```

- **Method 2:** Install via MSI package

- For more methods, refer to: [Microsoft - Installing PowerShell on Windows](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4)


### 1.2 Installing Python

- **Method 1:** Download the installer from the official Python website
    - [Python official downloads](https://www.python.org/downloads/)

    Go to your downloads folder, locate the installer, and double-click to start the installation.

    Choose the installation path as needed, and make sure to check "Add Python to PATH".


- **Method 2:** If you have already installed PowerShell, you can install Python using PowerShell:

    ```ps1
    winget install Python.Python.<version>  # Replace <version> with the version number, e.g., winget install Python.Python.3.11
    ```

After installation, open Command Prompt and enter `python --version` to verify the installation. If the version number appears, Python is installed successfully.

- [How to access Device Manager using shortcuts and cmd commands in Windows 10 and 11](https://www.dell.com/support/kbdoc/zh-tw/000123570/%E5%9C%A8-windows-10-%E5%92%8C-11-%E4%B8%AD%E4%BD%BF%E7%94%A8%E5%BF%AB%E9%80%9F%E9%8D%B5%E5%92%8C-cmd-%E5%91%BD%E4%BB%A4%E5%AD%98%E5%8F%96%E8%A3%9D%E7%BD%AE%E7%AE%A1%E7%90%86%E5%93%A1)

## 2. Usage Instructions

### 2.1 How to Set Up the Extraction Environment

**To use our service, you need to set up the required environment to facilitate log and data extraction.**

1. Step 1: Open Command Prompt or PowerShell as Administrator
    - [How to access Device Manager using shortcuts and cmd commands in Windows 10 and 11](https://www.dell.com/support/kbdoc/zh-tw/000123570/%E5%9C%A8-windows-10-%E5%92%8C-11-%E4%B8%AD%E4%BD%BF%E7%94%A8%E5%BF%AB%E9%80%9F%E9%8D%B5%E5%92%8C-cmd-%E5%91%BD%E4%BB%A4%E5%AD%98%E5%8F%96%E8%A3%9D%E7%BD%AE%E7%AE%A1%E7%90%86%E5%93%A1)

2. Step 2: Run install.bat

    ```
    .\install.bat
    ```

## FAQ
