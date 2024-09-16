## Update Dreamhost DNS With Local IP

Dockerfile & associated script for updating Dreamhost DNS A record on a domain with the
local IP address of the container. Helpful for maintaining an external access point to a home network.

## Docker Usage

Checkout the `docker-compose.yml` file for usage information.

https://hub.docker.com/r/iloveitaly/dreamhost-dns-updater

Want to execute the script within a running docker container (for debugging):

```shell
docker exec -it 2fdea37c57e6 bash
./dreampy_dns.py
```

## Command Line Usage

First, you need a [DreamHost API key](https://panel.dreamhost.com/?tree=home.api) with full DNS permissions.

Next, you'll need to set the API key and domain that will be updated. If you are updating a subdomain, you don't need to have the record pre-set in the Dreamhost UI.

You can execute the script in two ways:

* Update the variables within the python script
* Set the `DREAMHOST_API_KEY` and `DREAMHOST_UPDATE_DOMAIN` environment variables

Script runs from CLI in the usual way, eg.:

```shell
DREAMHOST_API_KEY=key DREAMHOST_UPDATE_DOMAIN=domain python3 ./dreampy_dns.py
```

Or you can run it directly after making it executable:

```
chmod +x ./dreampy_dns.py
./dreampy_dns.py
```

## IPv6

You can update your domain with an IPv6 (AAAA) record also, if you would like to do so.
In that case, CHECKIPV6 variable must be set to anything other than the default 0.

## Dreamhost API Can Block Your IP

Their security systems seem less than great and they have blocked my residential IP. Contacting support fixes the issue, but they don't understand the problem at first.

This is to say, if you are having trouble connecting to `https://api.dreamhost.com` it could be your specific residential IP address.

## Kudos

The script was copied + modified from [this script](https://github.com/gsiametis/dreampy_dns)

## Related

* https://github.com/clempaul/dreamhost-dynamic-dns
* https://github.com/gsiametis/dreampy_dns
