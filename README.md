# OTX_Siphon
Pulls pulses from AlienVault subscription list; parses and dumps indicators to csv file.

This script requires the OTX SDK to be installed.  You can do this using
"pip install OTXv2"

Note that you can use a cache directory setting in the config file, and if it is present
then the cached version of the OTX SDK will be used.  The first time the cached SDK is used, 
it may take some time to sync the cache, but after that it shouldn't be too bad,
and in general using the cached method results in a lot less requests to OTX
