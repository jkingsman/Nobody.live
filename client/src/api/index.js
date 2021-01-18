import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:5000'
});

export const getStreams = () => api.get(`/streams`);

const apis ={
    getStreams
};

export default apis