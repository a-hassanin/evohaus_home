#  Evohaus Home
Sensor to fetch all meter data for an apartment managed by evohaus

# Installation Steps

- **optional**  try it out with docker , before install it into your home assistant.

    ```
    docker run -p 8123:8123 --restart always -d --name homeassistant -v ${PWD}:/config   -e TZ=Australia/Melbourne   ghcr.io/home-assistant/home-assistant:latest
    ```

- copy the `evohaus_home` to the `custom_components` folder 
- restart
- add the following entry in `configuration.yaml`

    ```
        sensor:                
          - platform: evohaus_home
            username: !secret evohaus_home_user
            password: !secret evohaus_home_password  
    ```

- add the following secrets in `secrets.yaml`

    ```
    evohaus_home_user: 'H20WXX_XX'
    evohaus_home_password: 'XXXXXX'

    ```

-  restart 
