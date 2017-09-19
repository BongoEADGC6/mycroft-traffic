
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

"Hey Mycroft, how long is my trip to work?". 
This will return your travel time, and if there is any traffic how much there is.


## Supported Phrases/Entities
Currently the phrases are:
* Hey Mycroft, how long is my trip to X? (Where X is a configured POI)



## TODO
* Include required start or arrival time

## In Development
* Be able to query for non-configured locations. (i.e. "How close is the nearest bank?")


## Contributing

All contributions welcome:

* Fork
* Write code
* Submit pull request

