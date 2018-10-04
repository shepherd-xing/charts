
var coin = {
    template: '#coin'
}
var exchange = {
    template: '#exchange'
}

var routerObj = new VueRouter({
    routes: [
        {path: '/', redirect: '/coin'},
        {path: '/coin', component: coin},
        {path: '/exchange', component: exchange},
        //{path: '/chart', component: chart}
    ],
    //linkActiveClass: 'myActive'
})

const app = new Vue({
    el: '#app',
    data: {},
    methods: {},
    router: routerObj,
    components: {
        'waterfall': Waterfall.waterfall,
        'waterfall-slot': Waterfall.waterfallSlot,
    }
})