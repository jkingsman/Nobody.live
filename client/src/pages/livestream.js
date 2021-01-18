import React, { Component } from 'react';
import api from '../api';

class LiveStream extends Component {
    constructor(props) {
        super(props);
        this.state= {
            streams: []
        };
    }

    componentDidMount = async () => {
        await api.getStreams().then(streams => {
            console.log('streams', streams);
        })
    }

    render() {
        return (
            <div>
                LiveStream Component Init
            </div>
        )
    }
}

export default LiveStream;