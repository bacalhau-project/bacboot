import textwrap
import subprocess
import threading
import select,sys
from queue import Queue

# Helper functions
def print_wrapped(text):
    wrapper = textwrap.TextWrapper(width=80)
    wrapped_text = wrapper.fill(text).strip()
    print(wrapped_text)


def return_to_menu(main):
    # Wait up to 3 seconds for the user to enter any key.
    # If they make any input, return to the main menu.
    # After 3 seconds, return to the main menu anyways.
    print("Returning to the main menu in a few seconds (or press any key to skip straight there...)")
    # Wings doesn't actually understand this bit but it works. Thanks Copilot!
    i, o, e = select.select( [sys.stdin], [], [], 3 )
    if (i):
        print()
        main()
    else:
        print()
        main()


# Intro screen
def print_intro_screen():
    print(r"""
  _                     _ _                 
 | |                   | | |                
 | |__   __ _  ___ __ _| | |__   __ _ _   _ 
 | '_ \ / _` |/ __/ _` | | '_ \ / _` | | | |
 | |_) | (_| | (_| (_| | | | | | (_| | |_| |
 |_.__/ \__,_|\___\__,_|_|_| |_|\__,_|\__,_|
                                            
 a Compute over Data framework for public, transparent, and optionally verifiable computation

 ⚡️ 🔐 💸 🤓 💥 📚 🎆 ⚡️ 🔐 💸 🤓 💥 📚 🎆 ⚡️

 ><(((º>
""")
    print("\nWelcome to BacBoot! 🤖")
    print()
    print_wrapped("This is an installer/bootstrapper for deploying Bacalhau on a single computer, group of computers or across diverse infrastructure. Whether you just want to install the Bacalhau client, or you want to install a Bacalhau node or cluster, BacBoot is the fastest and easiest path to doing so.")
    print("\nWhat would you like to do?")
    print("""
1) Install Bacalhau
2) Verify an installation (UNIMPLEMENTED)
3) Find out more about BacBoot
4) Check if my system(s) are supported by BacBoot (UNIMPLEMENTED)
5) Uninstall Bacalhau (UNIMPLEMENTED)
""")


def print_install_options():
    print("\nIn order to install Bacalhau safely and cleanly, we're going to need a few prerequisites.")
    print_wrapped("BacBoot is primarily powered by Ansible, but it's also good for deploying Bacalhau on Docker, driving Terraform or deploying in the cloud. What would you like to do?")
    print()
    print_wrapped("(Whatever you choose, we'll let you pick between deployment modes - just the client, just a node, both, or some other options too!)")
    print()
    print_wrapped("Also, this installer can even remove Ansible afterwards if you don't want to have it long term!")
    print("""
1) Install Bacalhau using Ansible
2) Install Bacalhau using Docker (UNIMPLEMENTED)
3) Install Bacalhau in the cloud using Ansible and Terraform (UNIMPLEMENTED)
""")

# Installers
def install_using_ansible():
    print("Awesome, let's get started!")
    print("First, we need to install Ansible. This is a one-time thing, and we'll remove it after we're done if you want us to.")
    print("We'll also need to install a few other things, like Python 3 and pip3. You probably already have them installed!")
    print("(UNIMPLEMENTED) Not actually doing anything yet")
    return_to_menu(print_intro_screen)
    print()

# Install checkers and verifiers
def check_if_ansible_installed():
    print("Checking if Ansible is installed...")
    try:
        subprocess.check_output(["which", "ansible-playbook"])
        subprocess.check_output(["which", "ansible"])
        print("Ansible is installed.")
        return True
    except subprocess.CalledProcessError:
        print("Ansible is not installed.")
        return False

# Uninstallers
def uninstall_bacalhau():
    print("Let's uninstall Bacalhau. Whether you're done using it, or you just want to remove it, we can help you do that.")
    print("We're happy you chose to try it out either way! 🤗")
    print("(UNIMPLEMENTED) Not actually uninstalling Bacalhau yet")

def uninstall_ansible():
    print("Uninstalling Ansible...")
    print("(UNIMPLEMENTED) Not actually uninstalling Ansible yet")

def uninstall_docker():
    print("Uninstalling Docker...")
    print("(UNIMPLEMENTED) Not actually uninstalling Docker yet")

def uninstall_pip3():
    print("Uninstalling pip3...")
    print("(UNIMPLEMENTED) Not actually uninstalling pip3 yet")

# Main program loop itself
def main():
    while True:
        print_intro_screen()
        choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-4, q): ").strip()

        if choice.lower() == 'q':
            print("Quitting...")
            break

        if choice == '1':
            print_install_options()
            install_choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-3, q): ").strip()

            if install_choice.lower() == 'q':
                print("Quitting...")
                break

            if install_choice == '1':
                # Call the function to install Bacalhau using Ansible here
                print("Installing Bacalhau using Ansible...")
                install_using_ansible()
            elif install_choice == '2':
                print("Docker installation is not yet implemented.")
            elif install_choice == '3':
                print("Cloud installation using Ansible and Terraform is not yet implemented.")
            else:
                print("Invalid choice. Please try again.")  
        elif choice == '5':
            print("Uninstalling Bacalhau is not yet implemented.")
            uninstall_bacalhau()
            ansible_installed = check_if_ansible_installed()
            if ansible_installed():
                print("We detected an Ansible installation. Would you like to remove Ansible too?")
                uninstall_ansible_choice = input("Enter 'y' to uninstall Ansible, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_ansible_choice.lower() == 'y':
                    uninstall_ansible()
                else:
                    print("Leaving Ansible installed.")
            docker_installed = check_if_docker_installed()
            if docker_installed():
                print("We detected a Docker installation. Would you like to remove Docker too?")
                uninstall_docker_choice = input("Enter 'y' to uninstall Docker, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_docker_choice.lower() == 'y':
                    uninstall_docker()
                else:
                    print("Leaving Docker installed.")
            python3_pip_installed = check_if_python3_pip_installed()
            if python3_pip_installed():
                print("Finally, we noticed pip3 is installed. You probably DO want it, but if we installed it, we can remove it too.")
                print("Would you like to remove it? Please be careful with your choice if this system ran or runs things other than bacalhau.")
                uninstall_pip3_choice = input("Enter 'y' to uninstall pip3, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_pip3_choice.lower() == 'y':
                    uninstall_pip3()
                else:
                    print("Leaving pip3 installed.")
            print()
            print("Thanks again for trying out Bacalhau and BacBoot! 🤗")
            print("If you have any remaining questions or want to keep in touch with the project, check out our GitHub:")
            print("https://github.com/bacalhau-project/bacalhau")
            print("and feel free to talk to us on #bacalhau on the Filecoin Slack!")
            print("We would love to know what your experience was like, and we'd love to hear your feedback!")
            print("Thanks, and have a great day! ⚡")

        elif choice in ['2', '3', '4', '5']:
            print("This option is not yet implemented.")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()