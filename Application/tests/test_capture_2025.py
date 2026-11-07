from unittest.mock import patch
import forgely

class Window:
    _hWnd=123
    title='Agglou - Pandawa - 3.7.13.17 - Release'
    isMinimized=False
    width=1648
    height=928
    left=0
    top=0

def test_native_capture_used_when_forgely_focused():
    from PIL import Image
    cap=forgely.GameCapture()
    img=Image.new('RGB',(1648,928),'blue')
    with patch.object(forgely,'foreground_handle',return_value=456), \
         patch.object(forgely,'list_dofus_windows',return_value=[Window()]), \
         patch.object(forgely,'foreground_belongs_to_game',return_value=False), \
         patch.object(forgely,'capture_window_native',return_value=img) as native:
        result,title=cap.capture()
    assert result is img
    assert 'Agglou' in title
    native.assert_called_once_with(123,1648,928)

def test_no_ocr_on_unavailable_native_capture():
    cap=forgely.GameCapture()
    with patch.object(forgely,'foreground_handle',return_value=456), \
         patch.object(forgely,'list_dofus_windows',return_value=[Window()]), \
         patch.object(forgely,'foreground_belongs_to_game',return_value=False), \
         patch.object(forgely,'capture_window_native',return_value=None):
        try:
            cap.capture()
        except forgely.GameNotForeground:
            pass
        else:
            assert False,'Must reject unavailable capture'
