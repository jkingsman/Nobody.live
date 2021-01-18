import axios from 'axios';

const api = axios.create({
    baseURL: 'localhost:5000'
});

export const getStreams = () => api.get(`/streams`);

const apis ={
    getStreams
};

export default apis