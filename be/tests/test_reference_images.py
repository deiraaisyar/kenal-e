from be import inference


def test_hf_image_urls_encode_original_filenames(monkeypatch):
    monkeypatch.setattr(inference,'REFERENCE_IMAGE_BASE_URL','https://huggingface.co/datasets/owner/repo/resolve/revision/images')
    gallery=inference.Gallery.__new__(inference.Gallery)
    gallery.filenames=['Copy of PCB #1?.jpg','ponsél.jpeg']
    gallery.thumbs={}
    assert gallery.thumbnail(0).endswith('/Copy%20of%20PCB%20%231%3F.jpg')
    assert gallery.thumbnail(1).endswith('/pons%C3%A9l.jpeg')


def test_local_thumbnail_overrides_remote_image(monkeypatch,tmp_path):
    monkeypatch.setattr(inference,'DATA',tmp_path)
    monkeypatch.setattr(inference,'REFERENCE_IMAGE_BASE_URL','https://example.com/images')
    (tmp_path/'thumbnails').mkdir()
    (tmp_path/'thumbnails'/'small photo.jpg').write_bytes(b'test')
    gallery=inference.Gallery.__new__(inference.Gallery)
    gallery.filenames=['original.jpg']
    gallery.thumbs={'original.jpg':'small photo.jpg'}
    assert gallery.thumbnail(0)=='/api/thumbnails/small%20photo.jpg'


def test_remote_images_can_be_disabled(monkeypatch):
    monkeypatch.setattr(inference,'REFERENCE_IMAGE_BASE_URL','')
    gallery=inference.Gallery.__new__(inference.Gallery)
    gallery.filenames=['original.jpg']
    gallery.thumbs={}
    assert gallery.thumbnail(0) is None
