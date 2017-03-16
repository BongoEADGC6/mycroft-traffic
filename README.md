
# Traffic Skill for Mycroft

This is a skill to query travel times to points of interest (POIs) for
[Mycroft](https://mycroft.ai). 

## Installation

Clone the repository into your `~/.mycroft/skills` directory. Then install the
dependencies inside your mycroft virtual environment:

```
cd ~/.mycroft/skills
git clone https://github.com/BongoEADGC6/mycroft-traffic.git TrafficSkill
```

## Configuration
First, you need to obtain an API key from the Google Developers Console and enabling the Google Directions API.
This can be done by following [this link](https://console.developers.google.com/apis/api/directions_backend?project=).

Add a block to your `~/.mycroft/mycroft.conf` file like this:

```
"TrafficSkill": {
  "api_key": "REPLACETHISWITHKEYFROMGOOGLE",
  "pois": {
    "default": {
      "destinations": {
        "work": "1 Main Street, Beverly Hills, CA 90210"
      },
      "origins": {
        "home": "350 5th Ave, New York, NY 10118"
      }
    }
  }
}
```

## Usage


## TODO

 * Be able to query for non-configured locations.
