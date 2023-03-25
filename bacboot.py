#!/usr/bin/env python3
import textwrap
import subprocess
import select,sys,os

# Helper functions
def print_wrapped(text):
    wrapper = textwrap.TextWrapper(width=80)
    wrapped_text = wrapper.fill(text).strip()
    print(wrapped_text)


def return_to_menu():
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
5) Uninstall Bacalhau
""")


# Questionnaire
def begin_questionnaire():
    # We now know we have Ansible available to us, so let's gather information from the user about what they want to do.
    print("Let's get started! 🚀")
    print()
    print_wrapped("First, we need to know what you want to do. Do you want to install the Bacalhau client, the Bacalhau node, or both?")
    print()
    print("""
1) Install the Bacalhau client
2) Install a Bacalhau node
3) Install the Bacalhau client and setup a Bacalhau node
""")
    choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    # User wants to install just the client.
    if choice == "1":
        print("Installing the Bacalhau client...")
        print("We don't really need to know anything to proceed, unless you want to install a specific version of Bacalhau!")
        print("Press [ENTER] to proceed, or enter a version number to install a specific version of Bacalhau.")
        print()
        print("(If you're confused or don't know what to do here, just press ENTER!)")
        version = input("Enter a version number or press [ENTER] to proceed: ")
        if version == "":
            run_ansible_playbook("bacalhau-client.yml")
        else:
            # Modify /tmp/bacalhau-ansible/vars/overrides.yml to install a specific version of Bacalhau
            # We'll do that by setting the variable "bacalhau_version" to the version number the user entered.
            overrides_file = "/tmp/bacalhau-ansible/vars/overrides.yml"
            bacalhau_version = version.strip()  # Remove any leading/trailing whitespace

            if not os.path.exists(overrides_file):
                # If the overrides file does not exist, copy overrides.yml.dist to create it
                command = f"cp /tmp/bacalhau-ansible/vars/overrides.yml.dist {overrides_file}"
                os.system(command)

            # Modify the overrides file to set the bacalhau_version variable
            command = f"sed -i '' -e 's/^bacalhau_version:.*/bacalhau_version: \"{bacalhau_version}\"/' {overrides_file}"
            os.system(command)
            # Now that we have applied the correct overrides, let's proceed!
            run_ansible_playbook("bacalhau-client.yml")
    # User wants to install a node.
    elif choice == "2":
        print("Installing a Bacalhau node...")
        print("Are you installing the Bacalhau node locally? (NOTE: The only answer is yes, as BacBoot does not yet support installing a Bacalhau node on a remote server.)")
        print("Note that this is not a limitation of Bacalhau itself, just BacBoot while it it's in early development!")
        print()
        print("""
1) Yes
2) No
""")
        choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
        if choice == "1":
            print("Installing a Bacalhau node locally...")
            run_ansible_playbook("bacalhau-node.yml")
        elif choice == "2" or choice == "q":
            print("Installing a Bacalhau node remotely...")
            print("We don't support this yet, but we're working on it! 🚧")
            print("Please check back later!")
            return_to_menu()
    # User wants to install both.
    elif choice == "3":
        print("Installing the Bacalhau client and setting up a Bacalhau node...")
        run_ansible_playbook("bacalhau-client.yml")
        run_ansible_playbook("bacalhau-node.yml")
    elif choice == "q":
        print("You chose not to do anything. Returning to the main menu...")
        return_to_menu()
    else:
        print("Invalid input. Please try again.")
        begin_questionnaire()


# Ansible automation
def run_ansible_playbook(playbook):
    print("First, let's make sure we have a copy of the Ansible playbook for Bacalhau.")
    print("We'll clone the repository from GitHub if we don't already have it.")
    print("To keep things clean, we'll save the playbook to /tmp/bacalhau-ansible.")
    print("For security reasons, we will verify that the playbook is untouched before we run it!")
    # TODO (feat): Implement this check after we get signing going.
    # print("We'll also verify that the playbook is signed by the Bacalhau developers.")
    print("If you don't trust us, you can always check the source code yourself!")
    print()
    print("(If you're confused or this sounds scary, don't worry! We're just making sure you're safe.")
    print("In this case, it's probably safe for you to continue if we don't print any errors and abort.)")
    if os.path.isdir("/tmp/bacalhau-ansible"):
        print("We already have a copy of the playbook. We'll use that.")
        print("But for security, let's check it's a clean and legitimate copy from GitHub.")
        print("Checking...")
        # Change into the /tmp/bacalhau-ansible directory
        os.chdir("/tmp/bacalhau-ansible")
        # Check that the repository is clean
        if subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.DEVNULL).returncode != 0:
            print("The repository is not clean! Please check it and try again.")
            return_to_menu()
        # Check that the repository is up to date
        try:
            # Check if the local branch is behind the remote branch using 'git remote show origin'
            remote_output = subprocess.check_output(["git", "remote", "show", "origin"]).decode().strip()
            is_behind = "local out of date" in remote_output

            # Check if the local branch is behind the remote branch
            output = subprocess.check_output(["git", "diff", "--name-only", "@{u}"]).decode().strip()

            if is_behind or output:
                print("The repository is not up to date! Please check it and try again.")
                print("Actually, we'll try to update it for you now - just press [ENTER] to let us know that's okay.")
                print("(Or if you want to run it anyways with the current version, type current and press [ENTER].)")
                print("Alternatively, enter anything else and we will abort entirely.")
                print()
                print("If you're confused or don't know what to do here, just press [ENTER]!")
                # Check if the user wants to update the playbook
                choice = input()
                if choice == "":
                    print("Let's update it for you automatically.")
                    # Update the playbook and make sure we get a clean return code.
                    if subprocess.run(["git", "pull"], stdout=subprocess.DEVNULL).returncode != 0:
                        print("Something went wrong while trying to update the playbook. It's probably not safe for us to continue, so we won't.")
                        print("Please check it and try again.")
                        return_to_menu()
                    print("Updated successfully!")
                    print("Let's continue!")
                elif choice == "current":
                    print("Okay, we'll run it anyways with the current version.")
                else:
                    print("Okay, we'll abort entirely.")
                    return_to_menu()
            else:
                print("The repository is up to date!")
        except subprocess.CalledProcessError as e:
            print(f"Error checking Git repository status: {e}")
            return_to_menu()
        # # Check that the repository is signed by the Bacalhau developers
        # if subprocess.run(["git", "verify-commit", "HEAD"], stdout=subprocess.DEVNULL).returncode != 0:
        #     print("The repository is not signed by the Bacalhau developers! Please check it and try again.")
        #     return_to_menu()
        print("Checked successfully!")
        print("We'll now run the playbook. Thanks for being patient with us! 🙏")
    else:
        print("We don't have a copy of the playbook. We'll clone it from GitHub.")
        print("Cloning...")
        # Check that we have git installed!
        if subprocess.run(["which", "git"], stdout=subprocess.DEVNULL).returncode != 0:
            # TODO (feat): We can even handle installing Git for the user! Let's do that if we have to! :)
            print("We don't have git installed! Please install git and try again.")
            return_to_menu()
        # Clone the repository
        if subprocess.run(["git", "clone", "https://github.com/zorlin/bacalhau-playbook", "/tmp/bacalhau-ansible"], stdout=subprocess.DEVNULL).returncode != 0:
            print("We couldn't clone the repository. Please check your internet connection and try again.")
            return_to_menu()
        print("Cloned successfully!")
        print("We just pulled this copy, so it's probably legitimate. Future versions will check this more thoroughly!")
    print("Now, let's run the playbook!")
    print("We'll run it with the following command:")
    print("ansible-playbook -i /tmp/bacalhau-ansible/inventory /tmp/bacalhau-ansible/" + playbook)
    print("Before we run this playbook, are you connecting as root or have passwordless sudo on the remote machine? If not, we'll run with --ask-become-pass mode turned on.")
    print("If you're not sure, just hit enter and we'll ask you.")
    # Loop through this choice. If the user enters something invalid, we'll ask them again.
    while True:
        choice = input("Enter 'y' to run with --ask-become-pass, or enter 'n' to run without: ")
        if choice == "y":
            if subprocess.run(["ansible-playbook", "--become", "--ask-become-pass", "-i", "/tmp/bacalhau-ansible/inventory", "/tmp/bacalhau-ansible/" + playbook], stdout=subprocess.DEVNULL).returncode != 0:
                print("We couldn't run the playbook. If you are accessing a remote machine, please check your network connection and permissions and try again.")
                print("You'll especially want to check that you can access the remote machine using your SSH keys, that you have accepted the machine's host keys...")
                print("and that you have sudo/become permissions if needed.")
                print()
                print("(If you are feeling particularly adventurous - and be careful if you are - run the playbook by hand to see what's wrong.")
                print("Feel free to ask for help if you take this route! 🙏)")
                return_to_menu()
            break
        elif choice == "n":
            if subprocess.run(["ansible-playbook", "--become", "-i", "/tmp/bacalhau-ansible/inventory", "/tmp/bacalhau-ansible/" + playbook], stdout=subprocess.DEVNULL).returncode != 0:
                print("We couldn't run the playbook. If you are accessing a remote machine, please check your network connection and permissions and try again.")
                print("You'll especially want to check that you can access the remote machine using your SSH keys, that you have accepted the machine's host keys...")
                print("and that you have sudo/become permissions if needed.")
                print()
                print("(If you are feeling particularly adventurous - and be careful if you are - run the playbook by hand to see what's wrong.")
                print("Feel free to ask for help if you take this route! 🙏)")
                return_to_menu()
            break
        else:
            print("Invalid input. Please try again, or enter 'q' to return to the main menu.")
            continue

    print("We believe we ran that playbook successfully. Check it out, then press [ENTER] to continue or any other key to abort.")
    choice = input()
    if choice == "":
        print("Continuing...")
    else:
        print("Aborting...")
        return_to_menu()
    # TODO (bug): If we remove Ansible, we should remove the playbook too!


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

# Advanced installers
def install_using_ansible():
    print("Awesome, let's get started!")
    print("First, we need to install Ansible. This is a one-time thing, and we'll remove it after we're done if you want us to.")
    print("We'll also need to install a few other things, like Python 3 and pip3. You probably already have them installed!")
    print()
    is_ansible_installed = check_if_ansible_installed()
    if is_ansible_installed:
        print("We detected an existing Ansible installation. You're ready to rock already! 🎸🪨")
        begin_questionnaire()
    else:
        print("We didn't detect an existing Ansible installation. Let's install it now.")
        install_ansible()
        print("Awesome, Ansible was installed successfully! Let's rock! 🎸🪨")
        begin_questionnaire()
    return_to_menu()
    print()

# Basic installers
def install_ansible():
    print("How would you like to install Ansible?")
    print("""
    1) Install Ansible using pip3
    2) Install Ansible using my package manager
    """)
    choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    if choice == "1":
        print("Installing Ansible using pip3...")
        pip3_installed = check_if_pip3_installed()
        if pip3_installed:
            install_ansible_using_pip3()
        else:
            print("We'll need Python's pip3 tool installed before we can proceed. Is that okay with you?")
            choice = input("Enter 'y' to install pip3 or enter 'q' to quit without making any further changes: ")
            if choice == "y":
                install_pip3()
                install_ansible_using_pip3()
            elif choice == "q" or choice == "n":
                print("Would you like to try installing Ansible using your package manager instead?")
                choice = input("Enter 'y' to install Ansible using your package manager or enter 'q' to quit without making any further changes: ")
                if choice == "y":
                    install_ansible_using_package_manager()
                elif choice == "q" or choice == "n":
                    print("Okay, not installing Ansible. We can't proceed without it, so we'll simply return you to the main menu now 😃")
                    return_to_menu()
            else:
                print("Invalid input. Please try again, or enter 'q' to quit without making any further changes.")
                print("We'll try installing Ansible again from the beginning, thanks for your patience!")
                install_ansible()
    elif choice == "2":
        print("Installing Ansible using your package manager...")
        install_ansible_using_package_manager()
    elif choice == "q":
        # TODO: We can actually install the Bacalhau client without Ansible at all, bash style. We should offer a basic installer for just that
        # that does not require Ansible and offer the user the choice to just install a Bacalhau client using the basic installer.
        # In this way, the Python script can actually replace the main bash installer too!
        print("We're unfortunately (currently) unable to continue without installing Ansible. Feel free to change your mind!")
        return_to_menu()


def install_pip3():
    print("Installing pip3...")
    try:
        # TODO (bug): We should also support Red Hat based distros, this is too distro dependent. Ironically, Ansible would help us here but we don't have it yet.
        subprocess.check_output(["sudo", "apt", "install", "python3-pip"])
        print("pip3 installed successfully!")
    except subprocess.CalledProcessError:
        print("Unable to install pip3. Please try again, or ask us for help!")
        return_to_menu()


def install_ansible_using_pip3():
    print("Installing Ansible using pip3...")
    try:
        # Check if we are running as root, if not we need to use sudo
        if os.geteuid() != 0:
            subprocess.check_output(["sudo", "pip3", "install", "ansible-core"])
        else:
            subprocess.check_output(["pip3", "install", "ansible-core"])
        print("Ansible installed successfully!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Unable to install Ansible using pip3. Please try again.")
        return False

def install_ansible_using_package_manager():
    print("Installing Ansible using your package manager...")
    try:
        # TODO (bug): We should also support Red Hat based distros, this is too distro dependent. Ironically, Ansible would help us here but we don't have it yet.
        subprocess.check_output(["sudo", "apt", "install", "ansible"])
        print("Ansible installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Unable to install Ansible using your package manager. Please try again.")
        return_to_menu()
        return False

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

def check_if_docker_installed():
    print("Checking if Docker is installed...")
    try:
        # TODO (bug): If you have Podman installed, this check will succeed and technically should NOT!
        subprocess.check_output(["which", "docker"])
        print("Docker is installed.")
        return True
    except subprocess.CalledProcessError:
        print("Docker is not installed.")
        return False


def check_if_pip3_installed():
    print("Checking if pip3 is installed...")
    try:
        subprocess.check_output(["which", "pip3"])
        print("pip3 is installed.")
        return True
    except subprocess.CalledProcessError:
        print("pip3 is not installed.")
        return False


# Uninstallers
def uninstall_bacalhau():
    print("Let's uninstall Bacalhau. Whether you're done using it, or you just want to remove it, we can help you do that.")
    print("We're happy you chose to try it out either way! 🤗")
    print("(UNIMPLEMENTED) Not actually uninstalling Bacalhau yet")

def uninstall_ansible():
    print("Uninstalling Ansible...")
    print("This is an early version of the script, so we just want to check - how did we originally install Ansible?")
    print("""
    1) Installed Ansible using pip3
    2) Installed Ansible using my package manager
    """)
    choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    if choice == "1":
        uninstall_ansible_using_pip3()
    elif choice == "2":
        uninstall_ansible_using_package_manager()
    elif choice == "q":
        print("Did not uninstall Ansible or make any changes as you chose to quit. We'll continue the uninstallation process though, unless you want to quit.")
        print("To abort now, just press CTRL-C.")

def uninstall_ansible_using_pip3():
    print("Uninstalling Ansible using pip3...")
    try:
        # Check if we are running as root, if not, we need to use sudo
        if os.geteuid() != 0:
            subprocess.check_output(["sudo", "pip3", "uninstall", "-y", "ansible-core"])
        else:
            subprocess.check_output(["pip3", "uninstall", "-y", "ansible-core"])
        print("Ansible uninstalled successfully!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Unable to uninstall Ansible using pip3. Sorry! Please try again.")
        return False

def uninstall_ansible_using_package_manager():
    print("Uninstalling Ansible using your package manager...")
    # TODO (bug): We should also support Red Hat based distros, this is too distro dependent.
    # Ironically Ansible would help us here, but we're about to remove it so can't use it safely.

    # Uninstall Ansible, then check we succeeded in removing it.
    # Check if we are running as root, if not, we need to use sudo
    if os.geteuid() != 0:
        process = subprocess.run(["sudo", "apt", "remove", "-y", "ansible"])
    else:
        process = subprocess.run(["apt", "remove", "-y", "ansible"])
    try:
        # Check for the Ansible binary using "which", and return false if we still find it
        subprocess.check_output(["which", "ansible"])
        # If the subprocess returned true, then we still have Ansible installed, so we need to return false
        is_ansible_installed = True
    except subprocess.CalledProcessError:
        # If the subprocess raised an exception, that means "which" did not find Ansible, so it's uninstalled
        is_ansible_installed = False

    # Check if we succeeded in removing Ansible by examining the exit code and checking if Ansible is still installed
    if process.returncode == 0 and not is_ansible_installed:
        print("Ansible has been successfully uninstalled.")
        return True
    else:
        print("An error occurred during uninstallation. Ansible may still be installed.")
        return False


def uninstall_docker():
    print("Uninstalling Docker...")
    print("(UNIMPLEMENTED) Not actually uninstalling Docker yet")

def uninstall_pip3():
    print("Uninstalling pip3 using your package manager...")
    # TODO (feat) (good-first-issue): We can probably merge this and any other package install/uninstall scriptsto some extent with a bit of work. It'll reduce code smell.
    # TODO (bug): We should also support Red Hat based distros, this is too distro dependent.

    # Uninstall pip3, then check we succeeded in removing it.
    # Check if we are running as root, if not, we need to use sudo
    if os.geteuid() != 0:
        process = subprocess.run(["sudo", "apt", "remove", "-y", "python3-pip"])
    else:
        process = subprocess.run(["apt", "remove", "-y", "python3-pip"])
    try:
        # Check for the pip3 binary using "which", and return false if we still find it
        subprocess.check_output(["which", "pip3"])
        # If the subprocess returned true, then we still have pip3 installed, so we need to return false
        is_pip3_installed = True
    except subprocess.CalledProcessError:
        # If the subprocess raised an exception, that means "which" did not find pip3, so it's uninstalled
        is_pip3_installed = False
    
    # Check if we succeeded in removing pip3 by examining the exit code and checking if pip3 is still installed
    if process.returncode == 0 and not is_pip3_installed:
        print("pip3 has been successfully uninstalled.")
        return True
    else:
        print("An error occurred during uninstallation. pip3 may still be installed.")
        return False


# Main program loop itself
def main():
    while True:
        print_intro_screen()
        choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-4, q): ").strip()

        if choice.lower() == 'q':
            print("Quitting...")
            sys.exit(1)

        if choice == '1':
            print_install_options()
            install_choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-3, q): ").strip()

            if install_choice.lower() == 'q':
                print("Quitting...")
                sys.exit(1)

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
            print("Uninstalling Bacalhau is not yet fully implemented.")
            uninstall_bacalhau()
            is_ansible_installed = check_if_ansible_installed()
            if is_ansible_installed:
                print("We detected an Ansible installation. Would you like to remove Ansible too?")
                uninstall_ansible_choice = input("Enter 'y' to uninstall Ansible, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_ansible_choice.lower() == 'y':
                    uninstall_ansible()
                else:
                    print("Leaving Ansible installed.")
            is_docker_installed = check_if_docker_installed()
            if is_docker_installed:
                print("We detected a Docker installation. Would you like to remove Docker too?")
                uninstall_docker_choice = input("Enter 'y' to uninstall Docker, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_docker_choice.lower() == 'y':
                    uninstall_docker()
                else:
                    print("Leaving Docker installed.")
            is_pip3_installed = check_if_pip3_installed()
            if is_pip3_installed:
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
