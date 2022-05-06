import slidingWindow as sw
import timerList as tm

wnd = sw.SlidingWindow(3,[None for i in range(20)],21)
print(wnd)
wnd.move_window(3)
print(wnd)
wnd.put_data("1",21+5,2)
print(wnd)
wnd.put_data("1",21+3,0)
wnd.put_data("1",21+4,1)
wnd.put_data("2",21+4,1)
print(wnd)
wnd.move_window(3)
wnd.put_data("mlem",21,2)
print(wnd)