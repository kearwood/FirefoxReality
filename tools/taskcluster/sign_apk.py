# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
This script aligns as signs the apks using the options passed in.
"""
import getopt;
import glob
import os
import subprocess
import sys

v1_platforms = {
   'oculusvr3dofstore',
}

def main(name, argv):
   token = ''
   v1_token = ''
   sign_url = 'https://edge.stage.autograph.services.mozaws.net/sign'
   release = False
   feature_name = ''
   try:
      opts, args = getopt.getopt(argv,"hrt:c:f:")
   except getopt.GetoptError:
      print name + ' -t <token file name> -c <v1 token file name> -r -f <feature name>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print name + ' -t <token file name> -c <v1 token file name> -r -f <feature name>'
         sys.exit()
      elif opt in ("-c"):
         with open(arg, 'r') as tokenfile:
            v1_token = tokenfile.read().rstrip()
      elif opt in ("-t"):
         with open(arg, 'r') as tokenfile:
            token = tokenfile.read().rstrip()
      elif opt in ('-r'):
         sign_url = 'https://edge.prod.autograph.services.mozaws.net/sign'
         release = True
      elif opt in ('-f'):
         feature_name = arg.replace('/','-') + '-'

   if not release and v1_token != '':
      print "Warning, v1 signing is only supported in production"

   build_output_path = './app/build/outputs/apk'

   # Create folder for saving build artifacts
   artifacts_path = './builds'
   if not os.path.exists(artifacts_path):
      os.makedirs(artifacts_path)

   # Sign APKs
   for apk in glob.glob(build_output_path + "/*/*/*-unsigned.apk"):
      print "=" * 80
      cred = token
      target = apk.replace('-unsigned', '-signed')
      align = False

      if not release:
         target = target.replace('-release-', '-staging-' + feature_name)
      else:
         for platform in v1_platforms:
            if platform in target.lower():
               print "Using v1 signing on target:", target
               cred = v1_token
               align = True

      print "Signing", apk
      print "Target ", target
      cmd = ["curl", "-F", "input=@" + apk, "-o", target, "-H", "Authorization: " + cred, sign_url]

      try:
         print subprocess.check_output(cmd)
      except subprocess.CalledProcessError as err:
         cmd = ' '.join(err.cmd).replace(cred, "XXX")
         print "Signing apk failed:", cmd
         print "Output:", err.output
         sys.exit(err.returncode)

      if align:
         split = os.path.splitext(target)
         orig = target;
         target = split[0] + "-aligned" + split[1]
         print subprocess.check_output(["zipalign", "-f", "-v", "-p", "4", orig, target])

      print "Verifying", target
      print subprocess.check_output(['apksigner', 'verify', '--verbose', target])
      print "Archiving", target
      os.rename(target, artifacts_path + "/" + os.path.basename(target))
   print "=" * 80
   print "Done Signing"

if __name__ == "__main__":
   main(sys.argv[0], sys.argv[1:])
