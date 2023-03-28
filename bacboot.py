#!/usr/bin/env python3
import textwrap
import subprocess
import select,sys,os
import unicodedata
import argparse
import logging
import time

# Cruft used to improve autodetection of success and failure states
EMOJI_RANGES = [
    (0x1F601, 0x1F64F),
    (0x2702, 0x27B0),
    (0x1F680, 0x1F6C0),
    (0x1F170, 0x1F251)
]
EMOJI_CHARS = "".join([chr(c) for r in EMOJI_RANGES for c in range(r[0], r[1]+1)])
# We are not "re-looping" unless we enter the main loop twice
relooping = False

# Helper functions
def log_wrapped(text, level="info"):
    wrapper = textwrap.TextWrapper(width=80)
    wrapped_text = wrapper.fill(text).strip()

    # If we are using a log level that is not INFO, we need to use the logging.log() function instead of the logging.info() function.
    log_func = getattr(logging, level.lower(), logging.info)
    log_func(wrapped_text)

def has_emoji(line):
    for char in line:
        if "Emoji" in unicodedata.name(char, ""):
            return True
    return False


def return_to_menu():
    # Wait up to 3 seconds for the user to enter any key.
    # If they make any input, return to the main menu.
    # After 3 seconds, return to the main menu anyways.
    # Set relooping to true so we know we're about to loop back into the script
    global relooping
    relooping = True
    logging.info("Returning to the main menu in a few seconds (or press any key to skip straight there...)")
    # Wings doesn't actually understand this bit but it works. Thanks Copilot!
    i, o, e = select.select( [sys.stdin], [], [], 3 )
    if (i):
        logging.info("")
        main()
    else:
        logging.info("")
        main()


# Download, check and update the playbook repository
def get_and_check_playbook(args):
    logging.info("First, let's make sure we have a copy of the Ansible playbook for Bacalhau.")
    logging.info("We'll clone the repository from GitHub if we don't already have it.")
    logging.info("To keep things clean, we'll save the playbook to /tmp/bacalhau-ansible.")
    logging.info("For security reasons, we will verify that the playbook is untouched before we run it!")
    # TODO (feat): Implement this check after we get signing going.
    # logging.info("We'll also verify that the playbook is signed by the Bacalhau developers.")
    logging.info("")
    logging.info("(If you're confused or this sounds scary, don't worry! We're just making sure you're safe.")
    logging.info("In this case, it's probably safe for you to continue if we don't print any errors and abort.)")
    if os.path.isdir("/tmp/bacalhau-ansible"):
        if not args.silent:
            logging.info("We already have a copy of the playbook. We'll use that.")
            logging.info("But for security, let's check it's a clean and legitimate copy from GitHub.")
            logging.info("Checking...")
        # Change into the /tmp/bacalhau-ansible directory
        os.chdir("/tmp/bacalhau-ansible")
        # Check that the repository is clean
        if subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("The repository is not clean! Please check it and try again.")
            if args.silent:
                logging.error("You're running in silent mode, but it isn't safe for us to continue. Exiting now...")
                sys.exit(1)
            return_to_menu()
        # Check that the repository is up to date
        try:
            # Check if the local branch is behind the remote branch using 'git remote show origin'
            remote_output = subprocess.check_output(["git", "remote", "show", "origin"]).decode().strip()
            is_behind = "local out of date" in remote_output

            # Check if the local branch is behind the remote branch
            output = subprocess.check_output(["git", "diff", "--name-only", "@{u}"]).decode().strip()

            if is_behind or output:
                # Set a blank choice by default
                choice = ""

                logging.warning("The repository is not up to date! We'll try to update it for you now.")
                if not args.silent:
                    logging.info("Press [ENTER] to let us know that's okay.")
                    logging.info("(Or if you want to run it anyways with the current version, type current and press [ENTER].)")
                    logging.info("Alternatively, enter anything else and we will abort entirely.")
                    logging.info("")
                    logging.info("If you're confused or don't know what to do here, just press [ENTER]!")
                    # Check if the user wants to update the playbook
                    choice = input()
                if choice == "":
                    logging.info("Let's update it for you automatically.")
                    # Update the playbook and make sure we get a clean return code.
                    if subprocess.run(["git", "pull"], stdout=subprocess.DEVNULL).returncode != 0:
                        logging.error("Something went wrong while trying to update the playbook. It's probably not safe for us to continue, so we won't.")
                        logging.error("Please check it and try again.")
                        if args.silent:
                            logging.error("You're running in silent mode, but it isn't safe for us to continue. Exiting now...")
                        return_to_menu()
                    logging.info("Updated successfully!")
                    logging.info("Let's continue!")
                elif choice == "current":
                    logging.info("Okay, we'll run it anyways with the current version.")
                else:
                    logging.info("Okay, we'll abort entirely.")
                    return_to_menu()
            else:
                logging.info("The repository is up to date!")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error checking Git repository status: {e}")
            if args.silent:
                logging.error("You're running in silent mode, but it isn't safe for us to continue. Exiting now...")
                sys.exit(1)
            return_to_menu()
        # # Check that the repository is signed by the Bacalhau developers
        # if subprocess.run(["git", "verify-commit", "HEAD"], stdout=subprocess.DEVNULL).returncode != 0:
        #     logging.info("The repository is not signed by the Bacalhau developers! Please check it and try again.")
        #     return_to_menu()
        if not args.silent:
            logging.info("Checked successfully!")
    else:
        logging.warning("We don't have a copy of the playbook. We'll clone it from GitHub.")
        logging.info("Cloning...")
        # Check that we have git installed!
        if subprocess.run(["which", "git"], stdout=subprocess.DEVNULL).returncode != 0:
            # TODO (feat): We can even handle installing Git for the user! Let's do that if we have to! :)
            logging.error("We don't have git installed! Please install git and try again.")
            return_to_menu()
        # Clone the repository
        if subprocess.run(["git", "clone", "https://github.com/zorlin/bacalhau-playbook", "/tmp/bacalhau-ansible"], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't clone the repository. Please check your internet connection and try again.")
            return_to_menu()
        logging.info("Cloned successfully!")
        logging.info("We just pulled this copy, so it's probably legitimate. Future versions will check this more thoroughly!")

# Intro screen
def print_intro_screen():
    logging.info(r"""
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
    logging.info("\nWelcome to BacBoot! 🤖")
    logging.info("")
    log_wrapped("This is an installer/bootstrapper for deploying Bacalhau on a single computer, group of computers or across diverse infrastructure. Whether you just want to install the Bacalhau client, or you want to install Bacalhau node(s) or clusters, BacBoot is the fastest and easiest path to doing so.")
    logging.info("\nWhat would you like to do?")
    logging.info("""
1) Install or upgrade Bacalhau
2) Verify an installation of Bacalhau
3) Find out more about BacBoot
4) Check if my system(s) are supported by BacBoot (UNIMPLEMENTED)
5) Uninstall Bacalhau
""")

# Questionnaire
def begin_questionnaire(args):
    # We now know we have Ansible available to us, so let's gather information from the user about what they want to do.
    # Check if we're running in silent mode first
    if not args.silent:
        logging.info("Let's get started! 🚀")
        logging.info("")
    if args.unattended and not args.install == "node":
        choice = "client"
    elif args.unattended and args.install == "node":
        choice = "node"
    else:
        log_wrapped("First, we need to know what you want to do. Do you want to install just the Bacalhau client, or both Bacalhau and a node?")
        logging.info("")
        logging.info("(If you are upgrading Bacalhau, you can just run this install step and it will upgrade automatically!)")
        logging.info("")
        # TODO (feat): Allow installing the bacalhau client on multiple machines without deploying nodes
        logging.info("""1) Install the Bacalhau client locally
2) Install the Bacalhau client and setup Bacalhau node(s)
""")
        choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    # User wants to install just the client.
    if choice == "1" or choice == "client":
        if not args.silent:
            logging.info("Installing the Bacalhau client...")
        # If we know we have a specific version already, or the user is running in unattended mode, don't bother printing the related help text and just jump in.
        if args.version or args.unattended:
            if args.version:
                version = args.version
            if args.unattended:
                version = ""
        else:
            logging.info("We don't really need to know anything to proceed, unless you want to install a specific version of Bacalhau!")
            logging.info("Press [ENTER] to proceed, or enter a version number to install a specific version of Bacalhau.")
            logging.info("")
            logging.info("(If you're confused or don't know what to do here, just press ENTER!)")
            version = input("Enter a version number or press [ENTER] to proceed: ")
        if version == "" or version == "latest":
            # Set bacalhau_version to "latest" as we do not actually have a custom version specified.
            bacalhau_version = "latest"
            # Let's make sure that we undo any changes to the overrides file that might have been made previously.
            overrides_file = "/tmp/bacalhau-ansible/vars/overrides.yml"
            if os.path.exists(overrides_file):
                # Modify the overrides file to set the bacalhau_version variable
                command = f"sed -i.bak -e 's/^bacalhau_version:.*/bacalhau_version: \"{bacalhau_version}\"/' {overrides_file} && rm {overrides_file}.bak"
                os.system(command)
            # Now that we have applied the correct overrides, let's proceed!
            run_ansible_playbook("bacalhau-client.yml", args, inventory="localhost")
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
            command = f"sed -i.bak -e 's/^bacalhau_version:.*/bacalhau_version: \"{bacalhau_version}\"/' {overrides_file} && rm {overrides_file}.bak"
            os.system(command)
            # Now that we have applied the correct overrides, let's proceed!
            run_ansible_playbook("bacalhau-client.yml", args, inventory="localhost")
    # User wants to install a node.
    elif choice == "2" or choice in ["node", "nodes"]:
        logging.info("Installing Bacalhau node(s)...")
        logging.info("Are you installing a Bacalhau node locally, or remotely installing node(s)?")
        logging.info("")
        logging.info("""1) Local node
2) Remote node(s)
""")
        choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
        if choice == "1":
            logging.info("Installing a Bacalhau node locally...")
            run_ansible_playbook("bacalhau-node.yml", args, inventory="localhost")
        elif choice == "2":
            logging.info("Installing Bacalhau node(s) remotely...")
            logging.warning("This is under construction 🚧")
            logging.warning("Mind the dust, it's pretty experimental.")
            # If the user specified an inventory file, check if we can find it in the working directory.
            if args.inventory and not os.path.isabs(args.inventory):
                # Attempt to find the inventory file in the current working directory
                if os.path.exists(os.getcwd() + "/" + args.inventory):
                    args.inventory = os.getcwd() + "/" + args.inventory
                else: 
                    logging.error("Could not find the specified inventory file. Please try again.")
                logging.error("You must specify an absolute path to the inventory file with the --inventory flag to use this feature.")
                logging.error("Please use an absolute path instead and try again. Exiting...")
                sys.exit(1)
            # If the user did not specify an inventory file, ask them for one.
            elif not args.inventory:
                while True:
                    if not args.inventory:
                        logging.info("What inventory file would you like to use?")
                        args.inventory = input("Enter the name of or a path to the inventory file: ")
                    if args.inventory and not os.path.isabs(args.inventory):
                        # Attempt to find the inventory file in the current working directory
                        if os.path.exists(os.getcwd() + "/" + args.inventory):
                            args.inventory = os.getcwd() + "/" + args.inventory
                        else: 
                            logging.error("Could not find the specified inventory file. Please try again.")
                            # Clear the inventory argument so we can ask the user for it again.
                            args.inventory = ""
                    else:
                        break
                logging.info("Using inventory file: " + args.inventory)
                install_local_node = input("Would you also like to install the Bacalhau client on the machine running BacBoot? (y/n) ")
                get_and_check_playbook(args)
                logging.info("We'll now run the playbook. Thanks for being patient with us! 🙏")
                if install_local_node == "y":
                    logging.info("Installing the Bacalhau client on the machine running BacBoot...")
                    run_ansible_playbook("bacalhau-client.yml", args, inventory="localhost")
                logging.info("")
                run_ansible_playbook("bacalhau-node.yml", args, inventory=args.inventory)
            return_to_menu()
        elif choice == "q":
            logging.error("You chose not to do anything. Returning to the main menu...")
            args.install = None
            return_to_menu()
        else: 
            logging.error("Invalid input. Please try again.")
            begin_questionnaire(args)
    elif choice == "q":
        logging.error("You chose not to do anything. Returning to the main menu...")
        args.install = None
        return_to_menu()
    else:
        logging.error("Invalid input. Please try again.")
        begin_questionnaire(args)


# Ansible automation
def run_ansible_playbook(playbook, args, inventory, extraopts=None):
    # Run ansible-galaxy install -r requirements.yml
    if playbook == "bacalhau-client.yml":
        # We don't need to do anything here as the client does not require any Ansible roles or collections.
        # TODO (bug): Exception is remote nodes, we should handle that case.
        pass
    if playbook == "bacalhau-node.yml":
        logging.info("First, we'll run ansible-galaxy and install any required modules...")
        if subprocess.run(["ansible-galaxy", "install", "-r", "/tmp/bacalhau-ansible/requirements.yml"], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't install the required Ansible roles and collections. Please check your internet connection and try again.")
            return_to_menu()
    elif playbook == "cloud.yml":
        # Install the cloud-specific requirements.
        if subprocess.run(["ansible-galaxy", "install", "-r", "/tmp/bacalhau-ansible/requirements-cloud.yml"], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't install the required Ansible roles and collections. Please check your internet connection and try again.")
            return_to_menu()
    else:
        logging.warning("Couldn't figure out which specific requirements file to load, so using the generic one.")
        if subprocess.run(["ansible-galaxy", "install", "-r", "/tmp/bacalhau-ansible/requirements.yml"], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't install the required Ansible roles and collections. Please check your internet connection and try again.")
            return_to_menu()
    
    # Set final inventory path based on user input
    if inventory == "localhost":
        final_inventory_path = "/tmp/bacalhau-ansible/inventory"
    else:
        final_inventory_path = inventory
    logging.info("Now, let's run the playbook!")
    logging.info("We'll run it with the following command:")
    logging.info("ansible-playbook -i " + final_inventory_path + " /tmp/bacalhau-ansible/" + playbook)
    if args.unattended:
        # We are running unattended, so we'll assume the user doesn't want to run with --ask-become-pass if they haven't explicitly specified that.
        if not args.ask_become_pass:
            logging.info("You're running in unattended mode, so we'll assume you do not want to run Ansible using --ask-become-pass.")
            logging.info("If you want to run it with --ask-become-pass, please run BacBoot again and add --ask-become-pass.")
        else:
            logging.info("You're running in unattended mode, but you have set --ask-become-pass")
            logging.info("When prompted, enter your become/sudo password, and we'll continue in fully unattended mode from there if possible.")
    # If are not in unattended mode, ask the user if they want to run with --ask-become-pass mode turned on.
    else:
        logging.info("Before we run this playbook, are you connecting as root or have passwordless sudo on the remote machine? If not, we'll run with --ask-become-pass mode turned on.")
        logging.info("If you're not sure, just hit enter and we'll ask you.")
        while True:
            choice = input("Enter 'y' to run with --ask-become-pass, or enter 'n' to run without: ")
            if choice == "y":
                args.ask_become_pass = True
            elif choice == "n":
                pass
            else:
                logging.error("Invalid input. Please try again, or enter 'q' to return to the main menu.")
                continue
            break
    # Run the playbook
    if args.ask_become_pass:
        if subprocess.run(["ansible-playbook", "--become", "--ask-become-pass", "-i", final_inventory_path, "/tmp/bacalhau-ansible/" + playbook], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't run the playbook, or it didn't succeed. If you are accessing a remote machine, please check your network connection and permissions and try again.")
            logging.error("You'll especially want to check that you can access the remote machine using your SSH keys, that you have accepted the machine's host keys...")
            logging.error("and that you have sudo/become permissions if needed.")
            logging.error("")
            logging.error("(If you are feeling particularly adventurous - and be careful if you are - run the playbook by hand to see what's wrong.")
            logging.error("Feel free to ask for help if you take this route! 🙏)")
            return_to_menu()
    else:
        if subprocess.run(["ansible-playbook", "--become", "-i", final_inventory_path, "/tmp/bacalhau-ansible/" + playbook], stdout=subprocess.DEVNULL).returncode != 0:
            logging.error("We couldn't run the playbook. If you are accessing a remote machine, please check your network connection and permissions and try again.")
            logging.error("You'll especially want to check that you can access the remote machine using your SSH keys, that you have accepted the machine's host keys...")
            logging.error("and that you have sudo/become permissions if needed.")
            logging.error("")
            logging.error("(If you are feeling particularly adventurous - and be careful if you are - run the playbook by hand to see what's wrong.")
            logging.error("Feel free to ask for help if you take this route! 🙏)")
            return_to_menu()

    if args.unattended:
        # We're running in unattended mode, and we're pretty sure we succeeded, so let us simply continue.
        logging.info("We believe we ran that playbook successfully. Continuing as we are in unattended mode.")
        time.sleep(3)
        pass
    else:
        logging.info("We believe we ran that playbook successfully. Check it out, then press [ENTER] to continue or any other key to abort.")
        choice = input()
        if choice == "":
            logging.info("Continuing...")
        else:
            logging.error("Aborting...")
            return_to_menu()
    # TODO (bug): If we remove Ansible, we should remove the playbook too!

def print_install_options():
    logging.info("In order to install Bacalhau safely and cleanly, we're going to need a few prerequisites.")
    log_wrapped("BacBoot is primarily powered by Ansible, but it's also good for deploying Bacalhau on Docker, driving Terraform or deploying in the cloud. What would you like to do?")
    logging.info("")
    log_wrapped("(Whatever you choose, we'll let you pick between deployment modes - just the client, just a node, both, or some other options too!)")
    logging.info("")
    log_wrapped("Also, this installer can even remove Ansible afterwards if you don't want to have it long term!")
    logging.info("""
1) Install Bacalhau using Ansible
2) Install Bacalhau using Docker (UNIMPLEMENTED)
3) Install Bacalhau in the cloud using Ansible (UNIMPLEMENTED)
4) Install Bacalhau in the cloud using Terraform + Ansible (UNIMPLEMENTED)
""")

# Advanced installers
def install_using_ansible(args):
    if not args.silent:
        logging.info("Awesome, let's get started!")
        logging.info("First, we need to install Ansible. This is a one-time thing, and we'll remove it after we're done if you want us to.")
        logging.info("We'll also need to install a few other things, like Python 3 and pip3. You probably already have them installed!")
        logging.info("")
        is_ansible_installed = check_if_ansible_installed(args)
        if is_ansible_installed:
            logging.info("We detected an existing Ansible installation. You're ready to rock already! 🎸🪨")
            begin_questionnaire(args)
        else:
            logging.warning("We didn't detect an existing Ansible installation. Let's install it now.")
            install_ansible(args)
            logging.info("Awesome, Ansible was installed successfully! Let's rock! 🎸🪨")
            begin_questionnaire(args)
        # We presumably succeeded, so let's remove Ansible if the user wants us to.
        # TODO (feat): Implement post-installation removal of Ansible.
    else:
        # We are running in silent mode, simply install Ansible and pip3 if needed.
        is_ansible_installed = check_if_ansible_installed(args)
        if is_ansible_installed:
            begin_questionnaire(args)
        else:
            install_ansible(args)
            begin_questionnaire(args)

    logging.info("")

# Basic installers
def install_ansible(args):
    logging.info("How would you like to install Ansible?")
    logging.info("""
    1) Install Ansible using pip3
    2) Install Ansible using my package manager
    """)
    choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    if choice == "1":
        logging.info("Installing Ansible using pip3...")
        pip3_installed = check_if_pip3_installed(args)
        if pip3_installed:
            install_ansible_using_pip3()
        else:
            logging.info("We'll need Python's pip3 tool installed before we can proceed. Is that okay with you?")
            choice = input("Enter 'y' to install pip3 or enter 'q' to quit without making any further changes: ")
            if choice == "y":
                install_pip3()
                install_ansible_using_pip3()
            elif choice == "q" or choice == "n":
                logging.info("Would you like to try installing Ansible using your package manager instead?")
                choice = input("Enter 'y' to install Ansible using your package manager or enter 'q' to quit without making any further changes: ")
                if choice == "y":
                    install_ansible_using_package_manager()
                elif choice == "q" or choice == "n":
                    logging.error("Okay, not installing Ansible. We can't proceed without it, so we'll simply return you to the main menu now 😃")
                    return_to_menu()
            else:
                logging.error("Invalid input. Please try again, or enter 'q' to quit without making any further changes.")
                logging.error("We'll try installing Ansible again from the beginning, thanks for your patience!")
                install_ansible(args)
    elif choice == "2":
        logging.info("Installing Ansible using your package manager...")
        install_ansible_using_package_manager()
    elif choice == "q":
        # TODO: We can actually install the Bacalhau client without Ansible at all, bash style. We should offer a basic installer for just that
        # that does not require Ansible and offer the user the choice to just install a Bacalhau client using the basic installer.
        # In this way, the Python script can actually replace the main bash installer too!
        logging.info("We're unfortunately (currently) unable to continue without installing Ansible. Feel free to change your mind!")
        return_to_menu()


def install_pip3():
    logging.info("Installing pip3...")
    try:
        # TODO (bug): We should also support Red Hat based distros, this is too distro dependent. Ironically, Ansible would help us here but we don't have it yet.
        subprocess.check_output(["sudo", "apt", "install", "python3-pip"])
        logging.info("pip3 installed successfully!")
    except subprocess.CalledProcessError:
        logging.error("Unable to install pip3. Please try again, or ask us for help!")
        return_to_menu()


def install_ansible_using_pip3():
    logging.info("Installing Ansible using pip3...")
    try:
        # Check if we are running as root, if not we need to use sudo
        if os.geteuid() != 0:
            subprocess.check_output(["sudo", "pip3", "install", "ansible-core"])
        else:
            subprocess.check_output(["pip3", "install", "ansible-core"])
        logging.info("Ansible installed successfully!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Unable to install Ansible using pip3. Please try again.")
        return False

def install_ansible_using_package_manager():
    logging.info("Installing Ansible using your package manager...")
    try:
        # TODO (bug): We should also support Red Hat based distros, this is too distro dependent. Ironically, Ansible would help us here but we don't have it yet.
        subprocess.check_output(["sudo", "apt", "install", "ansible"])
        logging.info("Ansible installed successfully!")
        return True
    except subprocess.CalledProcessError:
        logging.error("Unable to install Ansible using your package manager. Please try again.")
        return_to_menu()
        return False

# Install checkers and verifiers
def check_if_ansible_installed(args):
    if not args.silent:
        print("Checking if Ansible is installed... ", end="")
        # Flush the screen buffer to ensure our message is displayed before the next one.
        sys.stdout.flush()
    try:
        subprocess.check_output(["which", "ansible-playbook"])
        subprocess.check_output(["which", "ansible"])
        if not args.silent:
            logging.info("found Ansible.")
        return True
    except subprocess.CalledProcessError:
        if not args.silent:
            logging.warning("Ansible is not installed.")
        return False

def check_if_docker_installed(args):
    logging.info("Checking if Docker is installed...")
    try:
        # TODO (bug): If you have Podman installed, this check will succeed and technically should NOT!
        subprocess.check_output(["which", "docker"])
        logging.info("Docker is installed.")
        return True
    except subprocess.CalledProcessError:
        logging.warning("Docker is not installed.")
        return False


def check_if_pip3_installed(args):
    logging.info("Checking if pip3 is installed...")
    try:
        subprocess.check_output(["which", "pip3"])
        logging.info("pip3 is installed.")
        return True
    except subprocess.CalledProcessError:
        logging.warning("pip3 is not installed.")
        return False


# Uninstallers
def uninstall_bacalhau(args):
    logging.info("Let's uninstall Bacalhau. Whether you're done using it, or you just want to remove it, we can help you do that.")
    logging.info("We're happy you chose to try it out either way! 🤗")
    logging.error("(UNIMPLEMENTED) Not actually uninstalling Bacalhau yet")

def uninstall_ansible(args):
    logging.info("Uninstalling Ansible...")
    logging.info("This is an early version of the script, so we just want to check - how did we originally install Ansible?")
    logging.info("""
    1) Installed Ansible using pip3
    2) Installed Ansible using my package manager
    """)
    choice = input("Enter your choice or enter 'q' to quit without making any further changes: ")
    if choice == "1":
        uninstall_ansible_using_pip3()
    elif choice == "2":
        uninstall_ansible_using_package_manager()
    elif choice == "q":
        logging.warning("Did not uninstall Ansible or make any changes as you chose to quit. We'll continue the uninstallation process though, unless you want to quit.")
        logging.warning("To abort now, just press CTRL-C.")

def uninstall_ansible_using_pip3(args):
    logging.info("Uninstalling Ansible using pip3...")
    try:
        # Check if we are running as root, if not, we need to use sudo
        if os.geteuid() != 0:
            subprocess.check_output(["sudo", "pip3", "uninstall", "-y", "ansible-core"])
        else:
            subprocess.check_output(["pip3", "uninstall", "-y", "ansible-core"])
        logging.info("Ansible uninstalled successfully!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Unable to uninstall Ansible using pip3. Sorry! Please try again.")
        return False

def uninstall_ansible_using_package_manager():
    logging.info("Uninstalling Ansible using your package manager...")
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
        logging.info("Ansible has been successfully uninstalled.")
        return True
    else:
        logging.error("An error occurred during uninstallation. Ansible may still be installed.")
        return False


def uninstall_docker():
    logging.info("Uninstalling Docker...")
    logging.error("(UNIMPLEMENTED) Not actually uninstalling Docker yet")

def uninstall_pip3():
    logging.info("Uninstalling pip3 using your package manager...")
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
        logging.info("pip3 has been successfully uninstalled.")
        return True
    else:
        logging.error("An error occurred during uninstallation. pip3 may still be installed.")
        return False

# Experimental cloud features! HERE BE DRAGONS.
def deploy_to_cloud():
    # "ruh roh"
    logging.warning("Oh god, we warned you. Really, you want to try this?")
    logging.warning("Well, okay... if you're sure...")
    logging.info("Alright, pick your poison, brave warrior. This will at least be fun.")
    logging.info("""1) Deploy to AWS
2) Deploy to GCP
3) Deploy to Azure
4) Deploy to DigitalOcean
5) Deploy to Linode
6) Deploy to Vultr
    """)
    logging.info("Actually, since we're in a hurry, and I'm being so obliging...")
    logging.info("you don't get a choice. DigitalOcean it is!")
    # We're just playing a bit here. DigitalOcean is the only provider we've implemented support for yet.
    deploy_to_digitalocean()

def deploy_to_digitalocean():
    ### DEBUG STUFF ###
    # Fetch my API token from ~/.digitalocean_api_token
    do_api_token = ""
    try:
        with open(os.path.expanduser("~/.digitalocean_api_token"), "r") as f:
            do_api_token = f.read()
    except FileNotFoundError:
        logging.error("Unable to find your DigitalOcean API token. Please create a file called ~/.digitalocean_api_token and paste your API token into it.")
        sys.exit(1)
    do_region = "sgp1"
    do_size = "s-2vcpu-4gb"
    do_image = "ubuntu-22-04-x64"
    ssh_public_key = ""
    do_number_of_machines = ""
    ### REMOVE LATER ###

    logging.info("We'll need to gather some info before we get started.")
    logging.info("First, we'll need your DigitalOcean API Personal Access Token.")
    logging.info("You can find this by going to https://cloud.digitalocean.com/account/api/tokens")
    logging.info("and clicking \"Generate New Token\". Give it a name, and make sure it has the \"Read\" and \"Write\" permissions.")
    while (not do_api_token) or (do_api_token.strip() == ""):
        do_api_token = input("Then, copy the token and paste it here, or press 'q' to abort: ")
        if do_api_token.lower() == 'q':
            sys.exit(1)
    logging.info("Next, we'll need to know what region you want to deploy to.")
    logging.info("You can find a list of regions here: https://developers.digitalocean.com/documentation/v2/#list-all-regions")
    logging.info("Just copy the slug for the region you want to deploy to.")
    while (not do_region) or (do_region.strip() == ""):
        do_region = input("Then, copy the slug and paste it here, or press 'q' to abort: ")
        if do_region.lower() == 'q':
            sys.exit(1)
    while (not do_number_of_machines) or (do_number_of_machines.strip() == ""):
        do_number_of_machines = input("How many machines do you want to deploy? ")
        if do_number_of_machines.lower() == 'q' or not do_number_of_machines.isdigit():
            print("Please enter a number... aborting.")
            sys.exit(1)
    logging.info("Finally, we'll need to know what size droplet you want to deploy.")
    logging.info("You can find a list of droplet sizes here: https://developers.digitalocean.com/documentation/v2/#list-all-sizes")
    logging.info("Just copy the slug for the size you want to deploy.")
    while (not do_api_token) or (do_api_token.strip() == ""):
        do_size = input("Then, copy the slug and paste it here, or press 'q' to abort: ")
        if do_size.lower() == 'q':
            sys.exit(1)
    logging.info("Pick an existing SSH public key to pre-deploy on the machines:")
    # List .pub files found in ~/.ssh/ and ask the user to pick one
    # TODO (feat) (good-first-issue): We should probably support other SSH key locations, like /etc/ssh/ssh_host_rsa_key.pub
    # TODO (feat) (good-first-issue): Check that the key is actually a valid choice
    while (ssh_public_key is not None and not ssh_public_key) or (ssh_public_key is not None and ssh_public_key.strip() == ""):
        ssh_dir = os.path.expanduser("~/.ssh/")
        ssh_public_keys = [os.path.join(ssh_dir, f) for f in os.listdir(ssh_dir) if f.endswith(".pub")]
        for i, key_file in enumerate(ssh_public_keys, start=1):
            logging.info(f"{i}) {key_file}")
        ssh_key_choice = int(input("Then, enter the number of the key you want to use: "))
        ssh_public_key = ssh_public_keys[ssh_key_choice - 1]

    print("DEBUG " + ssh_public_key)
    logging.info("Okay, we're ready to deploy to DigitalOcean!")
    logging.error("But I'm still in a bad mood, so nope, we won't. Sorry!")
    logging.info("...I'm just kidding. Let's do it!")

    run_ansible_playbook("cloud.yml", args, inventory="localhost", extraopts={
        "do_api_token": do_api_token,
        "do_region": do_region,
        "do_size": do_size,
        "do_image": do_image,
        "do_number_of_machines": do_number_of_machines,
        "ssh_public_key": ssh_public_key
    })

# Installation and functionality verification functions
def verify_client():
    # Run a Bacalhau job and get the results
    logging.info("Verifying that Bacalhau client is installed and working correctly...")
    try:
        # Run the command "bacalhau docker run ubuntu echo Hello World"
        command = ["bacalhau", "docker", "run", "ubuntu", "echo", "Hello World"]
        result = subprocess.run(command, capture_output=True, text=True)
        output_lines = result.stdout.split("\n")

        relevant_lines = [line for line in output_lines if "...." in line and any(char in EMOJI_CHARS for char in line)]
        if len(relevant_lines) == 0:
            logging.error("Bacalhau client verification failed.")
            choice = input("Would you like to know more about what went wrong? (print debug information) [y/n]: ")
            if choice.lower() == "y":
                logging.error(result.stderr)
                logging.error(result.stdout)
            return False
        else:
            for line in relevant_lines:
                if "✅" not in line:
                    logging.error("Bacalhau client verification failed.")
                    choice = input("Would you like to know more about what went wrong? (print debug information) [y/n]: ")
                    if choice.lower() == "y":
                        logging.error(result.stderr)
                        logging.error(result.stdout)
                    return False
            return True
    except subprocess.CalledProcessError as e:
        logging.error("Bacalhau client verification failed.")
        logging.error("Error code:", e.returncode)
        choice = input("Would you like to know more about what went wrong? (print debug information) [y/n]: ")
        if choice.lower() == "y":
            logging.error(e.stderr)
            logging.error(e.stdout)
        return False

def verify_bacalhau_installation(args):
    # Noop
    logging.error("DEBUG: Not actually verifying yet.")

# Main program loop itself
def main():
    global args
    # Load in arguments passed on the command line.
    parser = argparse.ArgumentParser(description="""\
Bacalhau Bootstrapper
    ><(((º>
A tool for installing, managing and maintaining Bacalhau from the edge to the cloud.
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--install", "--upgrade", nargs="?", const="client", default=None,
        help="Install or upgrade Bacalhau. In silent mode, will assume you want to install the client if you don't specify component(s) to install."
    )
    parser.add_argument("-u", "--uninstall", metavar="COMPONENT", nargs="?", const="all", default=None,
        help="Uninstall Bacalhau. In silent mode, will assume you want to uninstall the client if you don't specify component(s) to uninstall."
    )
    parser.add_argument(
    "-c", "--verify", nargs="?", const="client",
    help="Verify Bacalhau components and then exit. If no argument is passed, the client will be checked by default."
    )
    parser.add_argument("--cloud", help="Specify a cloud to deploy to or manage. If you don't specify a cloud, will use DigitalOcean.", default="do")
    parser.add_argument("--cloud-region", help="Specify a region to deploy to or manage. Mandatory if --cloud is set.")
    parser.add_argument("--inventory", help="Specify the inventory file to use. If unspecified, will simply default to localhost. Mandatory for remote deployments.")
    parser.add_argument("--user", help="[UNDER CONSTRUCTION] Specify the user to use for remote deployments. If unspecified, will default to the current user.")
    parser.add_argument("-a", "--unattended", help="Run in unattended mode, and make reasonable decisions withfout user input", action="store_true")
    parser.add_argument("-s", "--silent", help="Run in silent mode, suppressing all output except warnings, errors, and a report at the end. Implies --unattended.", action="store_true")
    parser.add_argument("--truly-silent", help="Run in truly silent mode, only outputting errors or prompts needed for authentication such as sudo. Implies --silent.", action="store_true")
    parser.add_argument("--dry-run", help="[UNIMPLEMENTED] Dry-run mode. Note that this WILL install Ansible on the machine running BacBoot. Can be combined with --remove-ansible.")
    parser.add_argument("-m", "--method", help="Specify the installation method to use. Default: Ansible.", choices=["ansible", "cloud", "docker", "direct"])
    parser.add_argument("--skip-verification", help="Always skip verification of the installed or upgraded components.", action="store_true")
    parser.add_argument("--ask-become-pass", help="Automatically ask for the sudo password when running Ansible.", action="store_true")
    parser.add_argument("--version", help="Specify a version of Bacalhau to install. Default: latest.", default="latest")
    parser.add_argument("--remove-pip3", help="Remove pip3 from the system", action="store_true")
    parser.add_argument("--remove-docker", help="Remove Docker from the system", action="store_true")
    parser.add_argument("--remove-ansible", help="Remove Ansible from the system, after doing any actions that require Ansible.", action="store_true")
    parser.add_argument("--experimental", help="Void the warranty and use experimental features. DO NOT USE THIS unless you know what you are doing!", action="store_true")

    args = parser.parse_args()

    # Set implied arguments and logging levels.

    # Configure the logging level and format
    if args.truly_silent:
        args.silent = True
        logging.basicConfig(level=logging.ERROR, format='%(message)s')
    if args.silent:
        args.unattended = True
        # Avoid overriding the truly silent mode's logging settings
        if not args.truly_silent:
            logging.basicConfig(level=logging.WARNING, format='%(message)s')
    else:
        # By default, show all INFO and above messages
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    while True:
        # Unconditionally define choice, as NoneType by default.
        choice = None
        if args.unattended:
            # If we're running unattended mode, make sure we have actions to do.
            if args.install is None and args.uninstall is None and args.verify is None:
                logging.error("No actions specified. Please specify an action to take in unattended mode.")
                sys.exit(1)
        # Detect if we have automatic actions to take, if we do don't ask the user for input and we break out of this loop.
        if (args.install or args.uninstall or args.verify) and not relooping:
            pass
        else:
            # Print the intro screen. Does nothing in silent modes.
            print_intro_screen()
            # Prompt the user for input if we're not running in unattended mode.
            choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-5, q): ").strip()

        # Checks if the user wants to bail.
        if choice is not None and choice.lower() == 'q':
            logging.error("Quitting...")
            sys.exit(1)
        if choice == '1' or (args.install and not relooping):
            if args.install:
                # Take the install choice from the command line argument
                if args.method:
                    install_choice = args.method
                else:
                    # Use the default installation method if nothing else was specified.
                    install_choice = "ansible"
            else:
                # Print the installation options and prompt the user for input.
                print_install_options()
                install_choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-3, q): ").strip()

            if install_choice is not None and install_choice.lower() == 'q':
                logging.error("Quitting...")
                sys.exit(1)

            if install_choice == '1' or install_choice == "ansible":
                # Call the function to install Bacalhau using Ansible here
                install_using_ansible(args)
                if not args.truly_silent:
                    print("Successfully installed Bacalhau using Ansible.")
            elif install_choice == '2' or install_choice == "docker":
                logging.error("Docker installation is not yet implemented.")
            elif install_choice == '3' or install_choice == "cloud":
                logging.error("Cloud installation using Ansible and Terraform is not yet implemented.")
                if not args.experimental:
                    # NO. THERE IS MORE. BUT YOU ARE NOT WORTHY. NOT YET.
                    return_to_menu()
                else:
                    logging.info("But since you look so pretty today, and you asked me nicely... hmm...")
                    logging.warning("This is under construction 🚧")
                    logging.warning("Mind the dust, it's pretty experimental.")
                    logging.warning("You have been warned!")
                    deploy_to_cloud()
                    logging.warning("We had joy, we had fun, etc. Thanks for playing, goodnight!")
                    sys.exit(1)

            else:
                logging.error("Invalid choice of install method. Please try again.")
            # If we made it this far, we should have a working installation of Bacalhau.
            if args.unattended:
                should_verify = not args.skip_verification
            else:
                logging.info("Do you want to verify the installation?")
                logging.info("Press [ENTER] to verify or any other key then [ENTER] to skip verification.")
                verify = input("Verify? ").strip()
                user_skipped = verify != ""
                should_verify = not user_skipped

            if should_verify:
                # Call the verification function here
                verify_bacalhau_installation(args)
            else:
                logging.warning("Skipping verification...")
            if args.remove_ansible:
                logging.info("Removing Ansible as requested after successful actions.")
                uninstall_ansible(args)
            if args.remove_pip3:
                logging.info("Removing pip3 as requested after successful actions.")
                uninstall_pip3(args)
            # Exit the loop.
            break

        # Verify an install
        if choice == '2' or args.verify:
            if args.skip_verification:
                logging.warning("Well ain't THAT clever? You've set --verify AND --skip-verification...")
                logging.warning("I'm gonna assume you're just making fun of me at this point, so we'll still verify the installation.")
            logging.info("Okay, we'll check if Bacalhau works. Do you want to test a client, a node or set of nodes, or both?")
            logging.info("""
    1) Bacalhau client
    2) Bacalhau node/cluster (also tests client)
    """)
            verify_choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-3, q): ").strip()
            # Loop through the menu until the user selects a valid option.
            while verify_choice not in ['1', '2', '3', 'q']:
                logging.error("Invalid choice of what to test. Please try again.")
                verify_choice = input("Enter your choice or enter 'q' to quit without making any further changes (1-3, q): ").strip()
            if verify_choice.lower() == 'q':
                logging.error("Quitting...")
                sys.exit(1)
            if verify_choice == '1':
                if verify_client():
                    logging.info("Looking good! You're all set. Enjoy! 🚀")
                    break
                else:
                    logging.error("Verification failed. 🎻😭 Bacalhau may be installed incorrectly. Please try again.")

                logging.info("Looking good! You're all set. Enjoy! 🚀")
                break
            elif verify_choice == '2':
                if verify_client() and verify_node():
                    logging.info("Looking good! You're all set. Enjoy! 🚀")
                    break
                else:
                    if not verify_client():
                        logging.error("We failed to verify the Bacalhau client.")
                    if not verify_node():
                        logging.error("We failed to verify the Bacalhau node or cluster.")
                    logging.error("Verification failed. 🎻😭 Bacalhau may be installed incorrectly. Please try again.")

        elif choice == '5':
            logging.error("Uninstalling Bacalhau is not yet fully implemented.")
            uninstall_bacalhau()
            is_ansible_installed = check_if_ansible_installed()
            if is_ansible_installed:
                logging.info("We detected an Ansible installation. Would you like to remove Ansible too?")
                uninstall_ansible_choice = input("Enter 'y' to uninstall Ansible, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_ansible_choice.lower() == 'y':
                    uninstall_ansible()
                else:
                    logging.info("Leaving Ansible installed.")
            is_docker_installed = check_if_docker_installed()
            if is_docker_installed:
                logging.info("We detected a Docker installation. Would you like to remove Docker too?")
                uninstall_docker_choice = input("Enter 'y' to uninstall Docker, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_docker_choice.lower() == 'y':
                    uninstall_docker()
                else:
                    logging.info("Leaving Docker installed.")
            is_pip3_installed = check_if_pip3_installed(args)
            if is_pip3_installed:
                # We use warning instead of info here intentionally as this is a dangerous action for some users.
                logging.warning("Finally, we noticed pip3 is installed. You probably DO want it, but if we installed it, we can remove it too.")
                logging.warning("Would you like to remove it? Please be careful with your choice if this system ran or runs things other than bacalhau.")
                uninstall_pip3_choice = input("Enter 'y' to uninstall pip3, or enter 'n' to keep it installed (y/n): ").strip()
                if uninstall_pip3_choice.lower() == 'y':
                    uninstall_pip3()
                else:
                    logging.warning("Leaving pip3 installed.")
            logging.info("")
            logging.info("Thanks again for trying out Bacalhau and BacBoot! 🤗")
            logging.info("If you have any remaining questions or want to keep in touch with the project, check out our GitHub:")
            logging.info("https://github.com/bacalhau-project/bacalhau")
            logging.info("and feel free to talk to us on #bacalhau on the Filecoin Slack!")
            logging.info("We would love to know what your experience was like, and we'd love to hear your feedback!")
            logging.info("Thanks, and have a great day! ⚡")

        elif choice in ['3', '4']:
            logging.error("This option is not yet implemented.")
        else:
            print("You entered: {}".format(choice))
            logging.error("Invalid choice of main task. Please try again.")

if __name__ == "__main__":
    main()
