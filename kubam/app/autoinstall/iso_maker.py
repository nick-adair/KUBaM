import os
import re
import random
import string
from subprocess import call
from shutil import rmtree
from config import Const


class IsoMaker(object):
    @staticmethod
    def list_isos(directory):
        """
        Takes in a hash of configuration data and validates to make surecit has the stuff we need in it.
        :param directory:
        :return: err, array
        """
        # Get all ISOs in a directory
        r = re.compile("iso$", re.IGNORECASE)

        try:
            files = os.listdir(directory)
        except OSError as err:
            return 1, err.strerror + ": " + err.filename
        list_of_isos = filter(r.search, files)
        return 0, list_of_isos

    @staticmethod
    def extract_iso(iso, mnt_dir):
        """
        Extract the ISO file into a directory call with iso file and directory to mount in:
        :param iso: /kubam/CentOS-7-x86_64-Minimal-1611.iso
        :param mnt_dir: /kubam/centos7.3
        :return: error code and message
        """
        err = 0
        if os.path.isdir(mnt_dir):
            return 1, mnt_dir + " directory already exists."
        # osirrox -prog kubam -indev ./*.iso -extract . centos7.3
        o = call(["osirrox", "-acl", "off", "-prog", "kubam", "-indev", iso, "-extract", ".", mnt_dir])
        if not o == 0:
            return 1, "error extracting ISO file.  Bad ISO file?"
        return err, "success"

    #  Change directory into the OS directory and determine what OS it actually is.
    @staticmethod
    def get_os(os_dir, iso):
        fname = os_dir + "/" + Const.OS_DICT[iso['os']]['key_file']
        if os.path.isfile(fname):
            f = object()
            try:
                f = open(fname, 'r')
            except OSError as err:
                # Permission denied error on ISO image.
                if err.errno == 13:
                    call(["chmod", "-R", "0755", os_dir])
                    call(["chmod", "0755", fname])
                    f = open(fname, "r")

            for line in f:
                if re.search(Const.OS_DICT[iso['os']]['key_string'], line):
                    return Const.OS_DICT[iso['os']]
        return None

    @staticmethod
    def mkboot_centos(os_name, version):
        boot_iso = "/kubam/" + os_name + version + "-boot.iso"
        if os.path.isfile(boot_iso):
            return 0, "boot iso was already created"
        os_dir = "kubam/" + os_name + version
        stage_dir = "/kubam/tmp/" + str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        o = call(["mkdir", "-p", stage_dir])
        if not o == 0:
            return 1, "Unable to make directory " + stage_dir
        o = call(["cp", "-a", os_dir + "/isolinux", stage_dir])
        if not o == 0:
            return 1, "Unable to copy /isolinux to {0}".format(stage_dir)
        o = call(["cp", "-a", os_dir + "/.discinfo", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /.discinfo to {0}".format(stage_dir)
        o = call(["cp", "-a", os_dir + "/LiveOS", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /LiveOS to {0}".format(stage_dir)
        o = call(["cp", "-a", os_dir + "/images/", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /images/ to {0}".format(stage_dir)
        o = call(["cp", "-a", "/usr/share/kubam/stage1/"+os_name+version+"/isolinux.cfg", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /isolinux.cfg to {0}".format(stage_dir)

        os.chdir("/kubam")
        o = 0
        if os_name == "centos":
            o = call([
                "mkisofs", "-o", boot_iso, "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot", "-V",
                "CentOS 7 x86_64", "-boot-load-size", "4", "-boot-info-table", "-r",
                "-J", "-v", "-T", stage_dir + "/isolinux"
            ])
        elif os_name == "redhat":
            o = call([
                "mkisofs", "-o", boot_iso, "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot", "-V",
                "RHEL-" + version + " Server.x86_64", "-boot-load-size", "4", "-boot-info-table", "-r",
                "-J", "-v", "-T", stage_dir + "/isolinux"
            ])

        if not o == 0:
            return 1, "mkisofs failed for {0}".format(boot_iso)
        return 0, "success"

    @staticmethod
    def mkboot_esxi():
        boot_iso = "/kubam/esxi6.5-boot.iso"
        if os.path.isfile(boot_iso):
            return 0, "boot iso was already created"
        os_dir = "kubam/esxi6.5"
        # Overwrite the boot directory
        o = call(["cp", "-a", "/usr/share/kubam/stage1/esxi6.5/BOOT.CFG", os_dir])
        if not o == 0:
            return 1, "Unable to copy /usr/share/kubam/stage1/esxi6.5/BOOT.CFG to {0}".format(os_dir)

        os.chdir("/kubam")
        # https://docs.vmware.com/en/VMware-vSphere/6.5/com.vmware.vsphere.install.doc/GUID-C03EADEA-A192-4AB4-9B71-9256A9CB1F9C.html
        o = call([
            "mkisofs", "-relaxed-filenames", "-J", "-R", "-o", boot_iso, "-b", "ISOLINUX.BIN", "-c", "boot.cat",
            "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table", "-no-emul-boot", os_dir
        ])
        if not o == 0:
            return 1, "Unable to create ISO image"

        return 0, "success"

    def mkboot(self, oper_sys):
        if oper_sys == "centos7.3":
            return self.mkboot_centos("centos", "7.3")
        elif oper_sys == "centos7.4":
            return self.mkboot_centos("centos", "7.4")
        elif oper_sys == "redhat7.2":
            return self.mkboot_centos("redhat", "7.2")
        elif oper_sys == "redhat7.3":
            return self.mkboot_centos("redhat", "7.3")
        elif oper_sys == "redhat7.4":
            return self.mkboot_centos("redhat", "7.4")
        return 0, "success"

    def mkboot_iso(self, isos):
        """
        Determine version of OS and make boot dir.
        :param isos: ISO images list
        :return: success or failure along with message
        """
        # Create random temporary directory
        err = 0
        msg = None
        for iso in isos:
            tmp_dir = "/kubam/tmp/"
            tmp_dir += str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            err, err_msg = self.extract_iso(iso['file'], tmp_dir)
            if err != 0:
                return err_msg, err
            o = self.get_os(tmp_dir, iso)
            if not o:
                return 1, "OS could not be determined with ISO image. Perhaps this is not a supported OS?"
            if not o["dir"] == iso["os"]:
                err_msg = "This ISO image seems to be {0} but you specified " \
                          "that it was {1}. Please change".format(o['dir'], iso['os'])
                return 1, err_msg
            # If the directory is already there, we don't touch it.
            if os.path.isdir("/kubam/" + o['dir']):
                print "removing temp"
                try:
                    rmtree(tmp_dir)
                except OSError as err:
                    # Permission denied error on ISO image.
                    if err.errno == 13:
                        call(["chmod", "-R", "0755", tmp_dir])
                        rmtree(tmp_dir)
            else:
                print "creating " + o['dir']
                try:
                    os.rename(tmp_dir, "/kubam/" + o['dir'])
                except OSError as err:
                    # Permission denied error on ISO image.
                    if err.errno == 13:
                        call(['chmod', '-R', '0755', tmp_dir])
                        os.rename(tmp_dir, "/kubam/" + o['dir'])
                    else:
                        return 1, err.strerror + ": " + err.filename

            # Now that we have tree, get boot media ready.
            err, msg = self.mkboot(o['dir'])
            # Remove tmp directory
            rmtree("/kubam/tmp")
        return err, msg